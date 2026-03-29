"""
map_player.py
-------------
Playback state and scheduling for the world map animation.
No Tkinter widgets, no Matplotlib, no data — pure control logic only.

Public API
----------
MapPlayer(root, on_frame_change, speed_ms=800)
    root             : tk.Tk  — needed for root.after() scheduling
    on_frame_change  : Callable[[int], None]  — called with year_idx on every frame
    speed_ms         : int  — milliseconds between frames during playback

Instance attributes
-------------------
.speed_ms              : int    — delay between frames; set freely at any time
.on_play_state_change  : Callable[[bool], None] | None
    Assign this after construction to receive play/pause state changes.
    Called with True when playback starts, False when it pauses.

Public methods
--------------
.play()               — start playback from current position
.pause()              — stop playback; keeps current position
.toggle()             — flip between play and pause
.step_forward()       — advance one year (pauses playback)
.step_back()          — retreat one year (pauses playback)
.jump_to(year_idx)    — jump to a specific year index (pauses playback)
"""

from __future__ import annotations
from typing import Callable

from map_data import YEARS


class MapPlayer:
    def __init__(
        self,
        root,
        on_frame_change: Callable[[int], None],
        speed_ms: int = 800,
    ):
        self._root            = root
        self._on_frame_change = on_frame_change
        self.speed_ms         = speed_ms

        self._year_idx:  int       = len(YEARS) - 1   # start at 2018
        self._playing:   bool      = False
        self._after_id:  str | None = None             # tk.after() handle

        # Optional hook — assign from map_view to sync the ▶/⏸ button icon
        self.on_play_state_change: Callable[[bool], None] | None = None

    # ── Public API ─────────────────────────────────────────────────────────────

    def play(self) -> None:
        """Start playback from the current position."""
        if self._playing:
            return
        self._set_playing(True)
        self._schedule_next()

    def pause(self) -> None:
        """Stop playback without moving position."""
        if not self._playing:
            return
        self._cancel_pending()
        self._set_playing(False)

    def toggle(self) -> None:
        """Flip between play and pause."""
        if self._playing:
            self.pause()
        else:
            self.play()

    def step_forward(self) -> None:
        """Advance one year and pause."""
        self.pause()
        self._go_to(min(self._year_idx + 1, len(YEARS) - 1))

    def step_back(self) -> None:
        """Retreat one year and pause."""
        self.pause()
        self._go_to(max(self._year_idx - 1, 0))

    def jump_to(self, year_idx: int) -> None:
        """
        Jump to a specific year index (0–15) and pause.
        Safe to call from the scrubber or external code.
        """
        self.pause()
        self._go_to(max(0, min(year_idx, len(YEARS) - 1)))

    # ── Internal ───────────────────────────────────────────────────────────────

    def _go_to(self, year_idx: int) -> None:
        """Move to year_idx and fire the render callback."""
        self._year_idx = year_idx
        self._on_frame_change(self._year_idx)

    def _advance(self) -> None:
        """
        Called by root.after() on each tick.
        Moves forward one year; wraps back to 2003 after 2018.
        """
        next_idx = self._year_idx + 1
        if next_idx >= len(YEARS):
            self.pause()
            return
        self._go_to(next_idx)

        # Re-schedule only if still playing (pause() may have cancelled us)
        if self._playing:
            self._schedule_next()

    def _schedule_next(self) -> None:
        """Schedule the next _advance() tick using the current speed."""
        self._after_id = self._root.after(self.speed_ms, self._advance)

    def _cancel_pending(self) -> None:
        """Cancel any pending root.after() call."""
        if self._after_id is not None:
            self._root.after_cancel(self._after_id)
            self._after_id = None

    def _set_playing(self, state: bool) -> None:
        """Update playing flag and notify the view hook if set."""
        self._playing = state
        if self.on_play_state_change is not None:
            self.on_play_state_change(state)