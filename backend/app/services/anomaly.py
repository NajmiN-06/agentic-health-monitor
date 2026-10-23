import numpy as np
from sklearn.ensemble import IsolationForest
from app.schemas import VitalsPayload

class AnomalyDetector:
    def __init__(self):
        # IsolationForest flags anomalies as -1 and normal points as 1
        self.model = IsolationForest(contamination=0.08, random_state=42)
        self._train_baseline_model()

    def _train_baseline_model(self):
        """
        Trains the model on 1,000 synthetic healthy physiological baseline samples.
        """
        np.random.seed(42)
        hr = np.random.normal(72, 4, 1000)
        bp_sys = np.random.normal(118, 5, 1000)
        bp_dia = np.random.normal(76, 4, 1000)
        spo2 = np.random.normal(98.2, 0.6, 1000)
        temp = np.random.normal(36.7, 0.2, 1000)

        X_train = np.column_stack((hr, bp_sys, bp_dia, spo2, temp))
        self.model.fit(X_train)
        print("[ML SERVICE] Isolation Forest model trained on baseline telemetry.")

    def predict(self, payload: VitalsPayload) -> tuple[bool, float]:
        """
        Evaluates a single telemetry payload.
        Returns:
            is_anomaly (bool): True if flagged as anomalous, False if normal.
            score (float): Decision function score.
        """
        features = np.array([[
            payload.heart_rate,
            payload.blood_pressure_sys,
            payload.blood_pressure_dia,
            payload.spo2,
            payload.temperature
        ]])

        prediction = self.model.predict(features)[0]  # 1 for normal, -1 for anomaly
        decision_score = self.model.decision_function(features)[0]

        is_anomaly = bool(prediction == -1)
        return is_anomaly, round(float(decision_score), 4)

# CRITICAL: This creates the singleton instance that main.py imports
anomaly_detector = AnomalyDetector()