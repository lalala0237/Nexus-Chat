import httpx
import asyncio
import platform

class UpdateManager:
    def __init__(self, current_version):
        self.current_version = current_version
        self.version_url = "https://lalala0237.github.io/NC-Updater/version.json"

    async def check_for_updates(self):
        try:
            # 加上时间戳防止 GitHub Pages 缓存
            url_with_cache = f"{self.version_url}?t={asyncio.get_event_loop().time()}"
            async with httpx.AsyncClient() as client:
                resp = await client.get(url_with_cache)
                data = resp.json()
                
                remote_version = data.get("latest_version")
                if remote_version != self.current_version:
                    return {
                        "has_update": True,
                        "new_version": remote_version,
                        "release_notes": data.get("release_notes", ""),
                        "download_url": self._get_platform_url(data.get("downloads", {}))
                    }
        except Exception as e:
            print(f"检查更新失败: {e}")
        return {"has_update": False}

    def _get_platform_url(self, downloads):
        os_name = platform.system().lower()
        if "windows" in os_name:
            return downloads.get("windows")
        elif "darwin" in os_name:
            return downloads.get("macos")
        elif "android" in os_name:
            return downloads.get("android")
        return None