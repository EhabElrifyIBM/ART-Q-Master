# Control Buttons - Visual Signal Flow Map

## Complete Signal Flow Diagram

```
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║                     PAUSE BUTTON SIGNAL FLOW (Example)                        ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  UI THREAD (Main Application Thread)                                              │
│                                                                                    │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │ 1. USER ACTION                                                             │  │
│  │                                                                            │  │
│  │    [⏸ PAUSE] ← User clicks button with mouse                            │  │
│  └────────────────────────┬─────────────────────────────────────────────────┘  │
│                           │                                                    │
│  ┌────────────────────────▼─────────────────────────────────────────────────┐  │
│  │ 2. BUTTON HANDLER EXECUTION (progress_monitor.py, line 453)              │  │
│  │                                                                            │  │
│  │    def _on_pause_clicked(self):                                          │  │
│  │        print("[DEBUG] Pause button clicked...")  ← Debug output          │  │
│  │        self._pause_flag = True                                           │  │
│  │        self.state = ProcessState.PAUSED                                  │  │
│  │        self.pause_btn.setEnabled(False)                                  │  │
│  │        self.resume_btn.setEnabled(True)                                  │  │
│  │        self.set_status("Status: ⏸ PAUSED...")                           │  │
│  │        self.log_warning("Process PAUSED by user")                        │  │
│  │        self.pause_requested.emit()  ← ★ KEY FIX: SIGNAL EMITTED        │  │
│  └────────────────────────┬─────────────────────────────────────────────────┘  │
│                           │                                                    │
│  ┌────────────────────────▼─────────────────────────────────────────────────┐  │
│  │ 3. UI UPDATED IMMEDIATELY                                                │  │
│  │                                                                            │  │
│  │    ✓ Pause button disabled (grayed out)                                 │  │
│  │    ✓ Resume button enabled (clickable)                                  │  │
│  │    ✓ Status label updated                                               │  │
│  │    ✓ Log message displayed                                              │  │
│  │                                                                            │  │
│  │    [Response Time: 1-5ms from click to visual feedback]                 │  │
│  └────────────────────────┬─────────────────────────────────────────────────┘  │
│                           │                                                    │
│  ┌────────────────────────▼─────────────────────────────────────────────────┐  │
│  │ 4. QT SIGNAL EMISSION                                                    │  │
│  │                                                                            │  │
│  │    self.pause_requested.emit()                                           │  │
│  │    ↓                                                                      │  │
│  │    Qt Event Loop receives signal                                         │  │
│  │    ↓                                                                      │  │
│  │    Routes to connected slot (lambda function)                           │  │
│  │                                                                            │  │
│  │    [Response Time: <1ms]                                                │  │
│  └────────────────────────┬─────────────────────────────────────────────────┘  │
│                           │                                                    │
│  ┌────────────────────────▼─────────────────────────────────────────────────┐  │
│  │ 5. LAMBDA FUNCTION EXECUTED (AutoSender_v2.py, line 809)                │  │
│  │                                                                            │  │
│  │    def on_pause():                                                       │  │
│  │        worker.set_pause(True)  ← Direct method call to worker          │  │
│  │        progress_monitor.log_warning("Process paused by user")           │  │
│  │                                                                            │  │
│  │    ✓ Calls method on worker object                                     │  │
│  │    ✓ Still on UI thread (no thread switch here)                        │  │
│  └────────────────────────┬─────────────────────────────────────────────────┘  │
│                           │                                                    │
│  ┌────────────────────────▼─────────────────────────────────────────────────┐  │
│  │ 6. WORKER METHOD CALLED (AutoSender_v2.py, line 116)                    │  │
│  │                                                                            │  │
│  │    def set_pause(self, paused):                                          │  │
│  │        print(f"[DEBUG] Worker: set_pause({paused}) called")             │  │
│  │        self._pause_flag = paused  ← FLAG SET (atomic operation)        │  │
│  │                                                                            │  │
│  │    ✓ Method receives call immediately                                  │  │
│  │    ✓ Flag is set atomically                                            │  │
│  │    ✓ Debug output logged                                               │  │
│  └────────────────────────┬─────────────────────────────────────────────────┘  │
│                           │                                                    │
└───────────────────────────┼────────────────────────────────────────────────────┘
                            │
                ┌───────────┴──────────┐
                │                      │
                ▼                      │
┌──────────────────────────────────────────────────────────────────────────────┐  
│  WORKER THREAD (Background Processing Thread)                               │  
│                                                                              │  
│  ┌──────────────────────────────────────────────────────────────────────┐  │  
│  │ 7. MAIN LOOP RUNNING CONCURRENTLY                                  │  │  
│  │                                                                     │  │  
│  │    while True:                                                     │  │  
│  │        for idx, row in self.df.iterrows():                        │  │  
│  │            │                                                       │  │  
│  │            ├─→ Check abort flag                                   │  │  
│  │            │                                                       │  │  
│  │            ├─→ Check pause flag ← ★ FLAG CHECK                   │  │  
│  │            │   if self._pause_flag:                              │  │  
│  │            │       print("[DEBUG] Pause flag detected...")       │  │  
│  │            │                                                       │  │  
│  │            │   while self._pause_flag:  ← ENTERS WAIT LOOP      │  │  
│  │            │       time.sleep(0.1)  ← CHECK EVERY 100ms          │  │  
│  │            │       if self._abort_flag:                          │  │  
│  │            │           break                                      │  │  
│  │            │                                                       │  │  
│  │            ├─→ Process case (SMS, Email, Notes)                  │  │  
│  │            │                                                       │  │  
│  │            └─→ Check stop flag (graceful exit)                   │  │  
│  │                                                                     │  │  
│  │    [Processing PAUSED in wait loop]                              │  │  
│  │    [Waits for flag to be cleared]                                │  │  
│  └──────────────────────────────────────────────────────────────────┘  │  
│                                                                         │  
│  ┌──────────────────────────────────────────────────────────────────┐  │  
│  │ 8. WAITING FOR RESUME (Pause State)                             │  │  
│  │                                                                     │  │  
│  │    Worker thread continuously checks:                            │  │  
│  │    ✓ Is _pause_flag still True?                                │  │  
│  │    ✓ Has user clicked Abort?                                   │  │  
│  │                                                                     │  │  
│  │    Every 100ms:                                                 │  │  
│  │    ├─ Check pause flag                                          │  │  
│  │    ├─ If abort detected, break                                  │  │  
│  │    └─ If pause cleared, exit loop                              │  │  
│  │                                                                     │  │  
│  │    [Processing is PAUSED - No case processing happening]       │  │  
│  │    [UI is RESPONSIVE - All buttons work normally]              │  │  
│  └──────────────────────────────────────────────────────────────────┘  │  
└──────────────────────────────────────────────────────────────────────────┘  

[Now if user clicks Resume button, signal flow repeats with set_pause(False)]

```

---

## Complete Control Button Signal Map

### All Four Buttons Signal Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                 Signal Connection Map                           │
│                                                                 │
│  BUTTON CLICK → HANDLER → SIGNAL EMIT → LAMBDA → WORKER      │
└─────────────────────────────────────────────────────────────────┘

PAUSE:
  [⏸ PAUSE] → _on_pause_clicked() → pause_requested.emit() 
              → on_pause() → worker.set_pause(True)
              → _pause_flag = True
              → Main loop enters wait loop

RESUME:
  [▶ RESUME] → _on_resume_clicked() → resume_requested.emit()
              → on_resume() → worker.set_pause(False)
              → _pause_flag = False
              → Main loop exits wait loop, continues

STOP:
  [⏹ STOP] → _on_stop_clicked() → [Dialog: "Continue?"]
              → stop_requested.emit()
              → on_stop() → worker.set_stop(True)
              → _stop_flag = True
              → Main loop breaks after current case

ABORT:
  [🛑 ABORT] → _on_abort_clicked() → [Warning: "Immediate?"]
              → abort_requested.emit()
              → on_abort() → worker.set_abort(True)
              → _abort_flag = True
              → Main loop breaks immediately

```

---

## Execution Timeline

```
Time    UI Thread                    Qt Signal Bus         Worker Thread
────────────────────────────────────────────────────────────────────────────

0ms     User clicks Pause            
        ├─ Handler runs             
        ├─ Set local state          
        ├─ Update UI buttons        
5ms     └─ emit() called             ──→ Signal queued
6ms                                      ──→ Lambda called
                                        └─→ worker.set_pause(True)
7ms                                                        Flag set
                                                          Check flag...
                                                          Flag=True!
100ms                                                      Check flag...
                                                          Still paused...
200ms   [UI still responsive]                             Check flag...
                                                          Still paused...
300ms   User clicks Resume           ──→ Signal queued
305ms   ├─ Handler runs              ──→ Lambda called
        ├─ Update UI                 └─→ worker.set_pause(False)
310ms   └─ resume_requested.emit()                        Flag cleared
                                                          Exit wait loop
                                                          Resume processing

```

---

## State Machine Diagram

```
                    ┌─────────────────────────┐
                    │   RUNNING (Initial)     │
                    │  Processing cases       │
                    │  _pause_flag = False    │
                    │  _stop_flag = False     │
                    │  _abort_flag = False    │
                    └───────────┬─────────────┘
                                │
                    ┌───────────┴──────────┐
                    │                      │
                    │ [PAUSE] clicked      │ [STOP] clicked
                    │                      │
                    ▼                      ▼
        ┌──────────────────────┐  ┌──────────────────────┐
        │  PAUSED              │  │  STOPPING            │
        │ Processing waits     │  │ Finishing case       │
        │ _pause_flag = True   │  │ _stop_flag = True    │
        │ _stop_flag = False   │  │ _pause_flag = False  │
        │ _abort_flag = False  │  │ _abort_flag = False  │
        └──────────┬───────────┘  └──────────┬───────────┘
                   │                         │
                   │ [RESUME]                │ [Current case
                   │ clicked                 │  completes]
                   │                         │
                   └─────────────┬───────────┘
                                 │
                                 ▼
                        ┌──────────────────────┐
                        │  STOPPED             │
                        │ Worker thread exit   │
                        │ Progress updated     │
                        │ Window waits OK      │
                        └──────────────────────┘
                        
                    At any time:
                    [ABORT] clicked
                        │
                        ▼
                    ┌──────────────────────┐
                    │  ABORTED             │
                    │ Immediate exit       │
                    │ _abort_flag = True   │
                    │ Worker thread exit   │
                    └──────────────────────┘

```

---

## Debug Output Sequence

```
User interactions and corresponding debug output:

1. PAUSE CLICKED:
   Console shows:
   [DEBUG] Pause button clicked - emitting pause_requested signal
   [DEBUG] Worker: set_pause(True) called
   [DEBUG] Worker: Pause flag detected - entering pause loop

2. WAIT (5 seconds):
   Console shows:
   [Silence - no log messages, just processing paused]

3. RESUME CLICKED:
   Console shows:
   [DEBUG] Resume button clicked - emitting resume_requested signal
   [DEBUG] Worker: set_pause(False) called
   [Processing resumes - log messages continue]

4. STOP CLICKED:
   Console shows:
   [DEBUG] Stop button confirmed - emitting stop_requested signal
   [DEBUG] Worker: set_stop(True) called
   Stop requested - gracefully exiting...
   [Worker thread finishes current case]
   Worker thread finished: Stopped

5. ABORT CLICKED:
   Console shows:
   [DEBUG] Abort button confirmed - emitting abort_requested signal
   [DEBUG] Worker: set_abort(True) called
   [DEBUG] Worker: Abort flag detected - breaking loop
   AutoSender aborted by user!
   Worker thread finished: Aborted

```

---

## Threading Interaction Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  Qt Application Event Loop (UI Thread)                      │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Progress Monitor Dialog                               │ │
│  │  ├─ Buttons always responsive                         │ │
│  │  ├─ Clicking buttons is instant                       │ │
│  │  ├─ UI updates don't block processing                 │ │
│  │  └─ Signals routed through Qt Event Queue            │ │
│  └───────────────────────────────────────────────────────┘ │
│                       ↓ Signal                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Lambda Functions                                      │ │
│  │  ├─ Receive signal                                    │ │
│  │  ├─ Call worker methods                               │ │
│  │  └─ Return immediately                                │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
     ↓ Direct method call (thread-safe)
┌─────────────────────────────────────────────────────────────┐
│  Worker Thread (Background Processing)                      │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Main Processing Loop                                  │ │
│  │  for each case:                                       │ │
│  │    ├─ Check flags                                     │ │
│  │    ├─ Process case (SMS, Email, etc)                  │ │
│  │    ├─ Emit progress signals                           │ │
│  │    └─ Update cache file                               │ │
│  │                                                        │ │
│  │ Flag Check Points:                                    │ │
│  │  ├─ Abort: At loop start (immediate break)           │ │
│  │  ├─ Pause: At case start (wait loop)                 │ │
│  │  └─ Stop: After case (graceful break)                │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

Key: UI Thread and Worker Thread run CONCURRENTLY
     Buttons can be clicked at ANY time
     Processing can be paused/resumed/stopped from any state

```

---

## Summary

This visual map shows:
1. ✅ How signals flow from button clicks to worker flags
2. ✅ When debug output appears during execution
3. ✅ How pause/resume/stop/abort work together
4. ✅ Thread interaction and concurrency
5. ✅ UI responsiveness maintained throughout

The key implementation detail that makes it all work:
**Signal emission (.emit() call) in button handlers**

Without this, signals never get emitted, so worker never gets notified.
With this, the complete chain works perfectly.
