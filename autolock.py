"""face-autolock: lock Windows only when the person actually leaves the desk.

Looking down, turning your head or leaning sideways does NOT lock the PC.
The screen locks only after a human who was sitting there has been gone
for a while.
"""

import argparse
import sys
import time

import cv2

CHECK_INTERVAL = 0.5  # seconds between camera checks (higher = less battery)


class PresenceTracker:
    """Pure logic (no camera, no OS calls) so it is easy to test.

    A human counts as present when a face (front or side) is seen, or when
    an upper body is seen shortly after a face (head down / reading).
    The tracker is only "armed" after a human has been seen, so it can never
    lock an empty room, and it locks once per departure.
    """

    def __init__(self, away_seconds: float = 10, body_grace: float = 60):
        self.away_seconds = away_seconds
        self.body_grace = body_grace
        self.armed = False
        self.last_human = None
        self.last_face = None

    def update(self, now: float, face: bool, body: bool, can_see: bool = True):
        """Return "armed", "lock" or None."""
        if face:
            self.last_face = now

        body_counts = (
            body and self.last_face is not None and now - self.last_face <= self.body_grace
        )
        if face or body_counts:
            self.last_human = now
            if not self.armed:
                self.armed = True
                return "armed"
            return None

        if not can_see:
            # Too dark / bad frame: we cannot tell, so never treat it as "left".
            if self.last_human is not None:
                self.last_human = now
            return None

        if self.armed and now - self.last_human > self.away_seconds:
            self.armed = False
            return "lock"
        return None


class Detector:
    def __init__(self):
        base = cv2.data.haarcascades
        self.frontal = self._load(base + "haarcascade_frontalface_default.xml")
        self.profile = self._load(base + "haarcascade_profileface.xml")
        self.upper = self._load(base + "haarcascade_upperbody.xml")

    @staticmethod
    def _load(path):
        cascade = cv2.CascadeClassifier(path)
        if cascade.empty():
            raise RuntimeError(f"Could not load cascade: {path}")
        return cascade

    def faces(self, gray):
        boxes = list(
            self.frontal.detectMultiScale(gray, 1.2, 5, minSize=(80, 80))
        )
        if not boxes:
            boxes += list(self.profile.detectMultiScale(gray, 1.2, 5, minSize=(80, 80)))
        if not boxes:
            # the profile model only sees one side, so also try the mirrored image
            width = gray.shape[1]
            flipped = self.profile.detectMultiScale(
                cv2.flip(gray, 1), 1.2, 5, minSize=(80, 80)
            )
            boxes += [(width - x - w, y, w, h) for (x, y, w, h) in flipped]
        return boxes

    def bodies(self, gray):
        return list(self.upper.detectMultiScale(gray, 1.1, 4, minSize=(120, 120)))


def lock_screen():
    import ctypes  # Windows only

    ctypes.windll.user32.LockWorkStation()


def main():
    parser = argparse.ArgumentParser(description="Lock Windows when you leave the desk")
    parser.add_argument("--away", type=float, default=10,
                        help="seconds without a human before locking (default 10)")
    parser.add_argument("--body-grace", type=float, default=60,
                        help="seconds an upper body keeps you 'present' after your face was last seen (default 60)")
    parser.add_argument("--min-brightness", type=float, default=25,
                        help="below this frame brightness (0-255) it is too dark to judge; never lock (default 25)")
    parser.add_argument("--camera", type=int, default=0, help="camera index (default 0)")
    parser.add_argument("--show", action="store_true", help="preview window, press q to quit")
    args = parser.parse_args()

    detector = Detector()
    tracker = PresenceTracker(args.away, args.body_grace)

    cap = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Could not open the camera. Is another app using it?")
        sys.exit(1)

    print(f"Running. Locks {args.away:g}s after you leave. Ctrl+C to stop.")
    try:
        while True:
            for _ in range(3):  # drop stale buffered frames
                cap.grab()
            ok, frame = cap.retrieve()
            if not ok:
                time.sleep(1)
                continue

            gray = cv2.equalizeHist(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
            can_see = cv2.mean(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))[0] >= args.min_brightness

            faces = detector.faces(gray) if can_see else []
            bodies = detector.bodies(gray) if can_see and not faces else []

            event = tracker.update(time.time(), bool(faces), bool(bodies), can_see)
            if event == "armed":
                print("Human detected, auto-lock armed.")
            elif event == "lock":
                print("You left -> locking.")
                lock_screen()

            if args.show:
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 229, 0), 2)
                for (x, y, w, h) in bodies:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (246, 92, 139), 2)
                state = "ARMED" if tracker.armed else "WAITING FOR A HUMAN"
                cv2.putText(frame, state, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.imshow("face-autolock", frame)
                if cv2.waitKey(int(CHECK_INTERVAL * 1000)) & 0xFF == ord("q"):
                    break
            else:
                time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
