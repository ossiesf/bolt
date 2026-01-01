import requests
import os
from datetime import datetime, timedelta
from typing import Optional

class GrafanaCapture:
    def __init__(self):
        self.grafana_url = os.getenv("GF_URL", "http://grafana:3000")
        self.api_key = os.getenv("GF_API_KEY")

    def capture_panel(
            self,
            dashboard_uid: str,
            panel_id: int,
            duration_minutes: int = 5,
            output_dir: str = "test-results/grafana"
    ) -> Optional[str]:
        """
        Capture a Grafana panel as PNG
        
        Args:
            dashboard_uid: Dashboard UID (e.g., 'main-fastapi')
            panel_id: Panel ID from the URL
            duration_minutes: Time range to capture
            output_dir: Where to save the image
            
        Returns:
            Path to saved image or None if failed
        """
        if not self.api_key:
            print("NO API KEY, skipping panel capture")
            return None

        os.makedirs(output_dir, exist_ok=True)
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(minutes=duration_minutes)).timestamp() * 1000)

        render_url = f"{self.grafana_url}/render/d-solo/{dashboard_uid}"

        params = {
            "orgId": 1,
            "panelId": panel_id,
            "from": start_time,
            "to": end_time,
            "width": 1200,
            "height": 400,
            "theme": "dark"
        }

        try:
            response = requests.get(
                render_url,
                params=params,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30
            )

            if response.status_code == 200:
                filename = f"panel_{panel_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                filepath = f"{output_dir}/{filename}"
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                return filename
            else:
                print(f"Failed to capture panel {panel_id}: {response.status_code}")
                return None
            
        except Exception as e:
            print(f"Error capturing panel {panel_id}: {e}")
            return None