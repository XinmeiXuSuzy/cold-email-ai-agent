from typing import Optional, Any
from app.config import settings

_langfuse = None


def get_langfuse():
    global _langfuse
    if _langfuse is None and settings.langfuse_public_key and settings.langfuse_secret_key:
        try:
            from langfuse import Langfuse
            _langfuse = Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host,
            )
        except Exception as e:
            print(f"[Langfuse] Failed to initialize: {e}")
    return _langfuse


class TraceContext:
    """Lightweight wrapper around a Langfuse trace."""

    def __init__(self, name: str, metadata: Optional[dict] = None):
        self.name = name
        self.metadata = metadata or {}
        self._trace = None
        self._trace_id: Optional[str] = None

    def start(self) -> str:
        lf = get_langfuse()
        if lf:
            self._trace = lf.trace(name=self.name, metadata=self.metadata)
            self._trace_id = self._trace.id
        return self._trace_id or "no-trace"

    def span(self, name: str, input: Any = None, output: Any = None, metadata: dict = None):
        if self._trace:
            self._trace.span(
                name=name,
                input=input,
                output=output,
                metadata=metadata or {},
            )

    def generation(
        self,
        name: str,
        model: str,
        prompt: Any,
        completion: Any,
        usage: Optional[dict] = None,
        metadata: dict = None,
    ):
        if self._trace:
            self._trace.generation(
                name=name,
                model=model,
                prompt=prompt,
                completion=completion,
                usage=usage,
                metadata=metadata or {},
            )

    def score(self, name: str, value: float, comment: Optional[str] = None):
        if self._trace:
            lf = get_langfuse()
            if lf and self._trace_id:
                lf.score(
                    trace_id=self._trace_id,
                    name=name,
                    value=value,
                    comment=comment,
                )

    def flush(self):
        lf = get_langfuse()
        if lf:
            lf.flush()
