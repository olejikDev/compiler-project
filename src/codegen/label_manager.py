# src/codegen/label_manager.py
"""Label management for control flow generation.
Sprint 6 requirements: COND-4, LOOP-1, LOOP-2
"""


class LabelManager:
    """Manages unique label generation for control flow."""

    def __init__(self):
        self.counter = 0
        self.label_stack = []

    def new_label(self, prefix: str = "L") -> str:
        """Generate a new unique label."""
        self.counter += 1
        return f"{prefix}{self.counter}"

    def push_loop(self, cond_label: str, end_label: str):
        """Push loop labels onto stack for break/continue."""
        self.label_stack.append({
            'cond': cond_label,
            'end': end_label,
            'continue': cond_label
        })

    def pop_loop(self):
        """Pop loop labels from stack."""
        if self.label_stack:
            return self.label_stack.pop()
        return None

    def get_break_label(self) -> str:
        """Get current break target."""
        if self.label_stack:
            return self.label_stack[-1]['end']
        return None

    def get_continue_label(self) -> str:
        """Get current continue target."""
        if self.label_stack:
            return self.label_stack[-1].get('continue', self.label_stack[-1]['cond'])
        return None

    def reset(self):
        """Reset label counter (for testing)."""
        self.counter = 0
        self.label_stack = []