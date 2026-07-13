"""
kubectl.py -- a READ-ONLY kubectl tool implementing the ATI Tool interface.

SECURITY DECISION: this tool only allows read verbs (get, describe, logs). It
deliberately cannot apply, delete, edit, scale, or exec. An LLM deciding on its own
to `kubectl delete deployment` is exactly the failure you do not want. If you later
want write access, add it explicitly and gate it -- do not open it by default.

Two things must be true for this tool to actually work in a pod:
  1. The `kubectl` binary must be present in the runtime image (add it to the Dockerfile).
  2. The pod's ServiceAccount must have RBAC permission to read the resources it queries.
     In-cluster, kubectl auto-uses the mounted ServiceAccount token; if the SA lacks
     permission, kubectl returns a "forbidden" error, which this tool surfaces as text.
"""

import subprocess

from .base import Tool

# Only these verbs are permitted. Anything else is refused before kubectl runs.
ALLOWED_VERBS = {"get", "describe", "logs"}


class KubectlTool(Tool):
    name = "kubectl"
    description = (
        "Run READ-ONLY kubectl commands to inspect the Kubernetes cluster. "
        "Supports: get (list resources), describe (details of one resource), "
        "logs (recent logs of a pod). Cannot modify, delete, or apply anything."
    )
    parameters = {
        "type": "object",
        "properties": {
            "verb": {
                "type": "string",
                "enum": ["get", "describe", "logs"],
                "description": "The read-only action to perform.",
            },
            "resource": {
                "type": "string",
                "description": (
                    "For get/describe: the resource type or name "
                    "(e.g. 'pods', 'deployments', 'pod/my-pod'). "
                    "For logs: the pod name."
                ),
            },
            "name": {
                "type": "string",
                "description": "Optional specific resource name (for get/describe).",
            },
            "namespace": {
                "type": "string",
                "description": "Kubernetes namespace. Defaults to 'default'.",
            },
        },
        "required": ["verb", "resource"],
    }

    def execute(self, args: dict) -> str:
        verb = args.get("verb", "")
        resource = args.get("resource", "")
        name = args.get("name")
        namespace = args.get("namespace", "default")

        # Guard: refuse anything not explicitly allowed. Defense in depth -- the
        # schema enum already restricts it, but never trust the model's output.
        if verb not in ALLOWED_VERBS:
            return f"error: verb {verb!r} is not permitted (read-only: get, describe, logs)"
        if not resource:
            return "error: 'resource' is required"

        # Build the command as a LIST, never a shell string. No shell=True means the
        # model cannot inject shell metacharacters (; | && etc) -- each argument is
        # passed verbatim to kubectl, not interpreted by a shell.
        cmd = ["kubectl", verb, resource]
        if name and verb in {"get", "describe"}:
            cmd.append(name)
        cmd += ["-n", namespace]
        if verb == "logs":
            cmd.append("--tail=50")  # cap log output so we don't flood the context

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,  # don't let a hung kubectl hang the agent forever
            )
        except FileNotFoundError:
            return "error: kubectl binary not found in the runtime image"
        except subprocess.TimeoutExpired:
            return "error: kubectl command timed out after 15s"

        if result.returncode != 0:
            # Return kubectl's own error (e.g. 'forbidden', 'not found') as text so
            # the model can see what went wrong and respond sensibly.
            return f"kubectl error:\n{result.stderr.strip()}"

        output = result.stdout.strip()
        return output if output else "(no output)"