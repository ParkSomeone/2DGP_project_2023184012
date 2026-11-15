import time


running = False
stack = []
frame_time = 0.0
simulation_scale = 1.0
frame_duration = 1.0 / 60.0


def change_mode(mode):
    if stack:
        stack.pop().finish()
    stack.append(mode)
    mode.init()


def push_mode(mode):
    if stack:
        stack[-1].pause()
    stack.append(mode)
    mode.init()


def pop_mode():
    if stack:
        stack.pop().finish()
    if stack:
        stack[-1].resume()
    else:
        quit()


def quit():
    global running
    running = False


def run(start_mode):
    global running, stack, frame_time, simulation_scale
    running = True
    stack = [start_mode]
    frame_time = 0.0
    simulation_scale = 1.0
    previous_time = time.perf_counter()
    try:
        start_mode.init()
        while running and stack:
            current_time = time.perf_counter()
            frame_time = max(0.0, current_time - previous_time)
            previous_time = current_time
            stack[-1].handle_events()
            if running and stack:
                stack[-1].update()
                stack[-1].render()
            remaining_frame_time = frame_duration - (
                time.perf_counter() - current_time
            )
            if remaining_frame_time > 0:
                time.sleep(remaining_frame_time)
    finally:
        while stack:
            stack.pop().finish()
        running = False
        simulation_scale = 1.0
