from locust import HttpUser, task, between

class URLShortnerUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def test_flow(self):
        # POST to shorten
        response = self.client.post("/shorten", json={"url": "https://google.com"})
        
        # If successful, try the redirect
        if response.status_code == 200:
            short_code = response.json().get("short_code")
            if short_code:
                self.client.get(f"/get/{short_code}", allow_redirects=False)