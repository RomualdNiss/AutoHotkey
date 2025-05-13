import time
from threading import Thread, Event
from pynput import mouse, keyboard

recording = False
is_playing = False
stop_playback = Event()
events    = []
last_time = 0.0

mouse_ctrl    = mouse.Controller()
keyboard_ctrl = keyboard.Controller()

# --- Capteurs souris --- #
def on_move(x, y):
    global last_time
    if not recording: return
    now = time.time()
    events.append(("move", (x, y), now - last_time))
    last_time = now

def on_click(x, y, button, pressed):
    global last_time
    if not recording: return
    now = time.time()
    events.append(("click", (x, y, button, pressed), now - last_time))
    last_time = now

def on_scroll(x, y, dx, dy):
    global last_time
    if not recording: return
    now = time.time()
    events.append(("scroll", (x, y, dx, dy), now - last_time))
    last_time = now

# --- Capteurs clavier --- #

def on_press(key):
    global last_time
    # F9 = enregistrement
    if key == keyboard.Key.f9:
        toggle_recording()
        return
    # F10 =  lecture
    if key == keyboard.Key.f10:
        toggle_playback()
        return

    if not recording: return
    now = time.time()
    events.append(("key_press", key, now - last_time))
    last_time = now

def on_release(key):
    global last_time
    if not recording: return
    now = time.time()
    events.append(("key_release", key, now - last_time))
    last_time = now

# --- Toggle --- #

def toggle_recording():
    global recording, events, last_time
    if not recording:
        events.clear()
        last_time = time.time()
        recording = True
        print("⏺ Enregistrement démarré")
    else:
        recording = False
        print(f"⏹ Enregistrement stoppé ({len(events)} événements)")

def toggle_playback():
    global is_playing, stop_playback
    if is_playing:
        # demander l'arrêt
        stop_playback.set()
        print("Arrêt de la lecture demandé…")
    else:
        if not events:
            print("⚠ Aucune macro à jouer.")
            return
        stop_playback.clear()
        Thread(target=playback, daemon=True).start()

def playback():
    global is_playing
    print("▶ Lecture démarrée")
    is_playing = True
    prev_x = prev_y = None

    for etype, data, delay in events:
        # si on a demandé l'arrêt, on sort  #
        if stop_playback.is_set():
            print("⏸ Lecture interrompue")
            break

        time.sleep(delay)

        if etype == "move":
            x, y = data
            # pour jeux plein écran, on envoie les deltas plutôt que la position absolue #
            if prev_x is None:
                prev_x, prev_y = x, y
            else:
                dx, dy = x - prev_x, y - prev_y
                mouse_ctrl.move(dx, dy)
                prev_x, prev_y = x, y

        elif etype == "click":
            x, y, btn, pressed = data
            mouse_ctrl.position = (x, y)
            if pressed:   mouse_ctrl.press(btn)
            else:         mouse_ctrl.release(btn)

        elif etype == "scroll":
            x, y, dx, dy = data
            mouse_ctrl.position = (x, y)
            mouse_ctrl.scroll(dx, dy)

        elif etype == "key_press":
            keyboard_ctrl.press(data)

        elif etype == "key_release":
            keyboard_ctrl.release(data)

    else:
        # boucle terminée normalement #
        print("▶ Lecture terminée")

    is_playing = False

# --- Démarrage des listeners --- #

mouse_listener = mouse.Listener(on_move=on_move,
                                on_click=on_click,
                                on_scroll=on_scroll)
keyboard_listener = keyboard.Listener(on_press=on_press,
                                      on_release=on_release)

mouse_listener.start()
keyboard_listener.start()

print("F9 = lancer/arrêter enregistrement — F10 = lancer/arrêter la lecture")
keyboard_listener.join()
