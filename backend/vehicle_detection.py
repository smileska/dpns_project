import cv2
import numpy as np
from time import sleep

MIN_CONTOUR_AREA = 500
WIDTH_MIN = 80
HEIGHT_MIN = 80
OFFSET = 15
POS_LINE = 550
DELAY = 30


def calculate_center(x, y, w, h):
    return (int(x + w / 2), int(y + h / 2))


def get_direction(y, prev_y):
    if prev_y is None:
        return None
    return 'up' if y < prev_y else 'down'


def process_frame(frame, subtractor):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 5)
    mask = subtractor.apply(blur)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    roi_mask = np.zeros_like(mask)
    roi_mask[200:700, 0:1200] = 255
    return cv2.bitwise_and(mask, roi_mask)


def detect_vehicles(frame, mask, vehicles, vehicle_count, next_vehicle_id):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    frame_center = frame.shape[1] // 2
    detection_zone = (POS_LINE - OFFSET, POS_LINE + OFFSET)

    for contour in contours:
        if cv2.contourArea(contour) < MIN_CONTOUR_AREA:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        if w < WIDTH_MIN or h < HEIGHT_MIN:
            continue

        center = calculate_center(x, y, w, h)

        new_vehicle = True
        for vehicle_id, vehicle_data in vehicles.items():
            dist = np.linalg.norm(np.array(center) - np.array(vehicle_data['center']))
            if dist < 50:
                new_vehicle = False
                vehicles[vehicle_id]['center'] = center
                vehicles[vehicle_id]['last_seen'] = 0

                direction = get_direction(center[1], vehicle_data['prev_y'])
                if direction:
                    vehicles[vehicle_id]['direction'] = direction

                if detection_zone[0] < center[1] <= detection_zone[1] and not vehicle_data['counted']:
                    vehicle_count[vehicles[vehicle_id]['direction']] += 1
                    vehicles[vehicle_id]['counted'] = True

                break

        if new_vehicle:
            vehicles[next_vehicle_id] = {
                'center': center,
                'last_seen': 0,
                'counted': False,
                'direction': None,
                'prev_y': None
            }
            next_vehicle_id += 1

    vehicles_to_remove = []
    for vehicle_id, vehicle_data in vehicles.items():
        vehicle_data['last_seen'] += 1
        vehicle_data['prev_y'] = vehicle_data['center'][1]
        if vehicle_data['last_seen'] > 10:
            vehicles_to_remove.append(vehicle_id)

    for vehicle_id in vehicles_to_remove:
        del vehicles[vehicle_id]

    return next_vehicle_id


def process_video(video_path):
    cap = cv2.VideoCapture(video_path)
    subtractor = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=16, detectShadows=False)

    vehicle_count = {'up': 0, 'down': 0}
    vehicles = {}
    next_vehicle_id = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        mask = process_frame(frame, subtractor)
        next_vehicle_id = detect_vehicles(frame, mask, vehicles, vehicle_count, next_vehicle_id)

        sleep(1 / DELAY)

    cap.release()
    return vehicle_count