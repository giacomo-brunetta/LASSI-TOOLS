import json
import psutil
import asyncio

async def get_info():
    def _get_info():
        cpu_freq = psutil.cpu_freq()
        cpu_info = {
            "count_logical": psutil.cpu_count(logical=True),
            "count_physical": psutil.cpu_count(logical=False),
            "frequency_mhz": cpu_freq._asdict() if cpu_freq else "N/A",
            "usage_percent": psutil.cpu_percent(interval=0.1)
        }
        
        vm = psutil.virtual_memory()
        ram_info = {
            "total_gb": round(vm.total / (1024**3), 2),
            "available_gb": round(vm.available / (1024**3), 2),
            "used_gb": round(vm.used / (1024**3), 2),
            "usage_percent": vm.percent
        }
        
        return {
            "cpu": cpu_info,
            "ram": ram_info
        }

    info = await asyncio.to_thread(_get_info)
    print(json.dumps(info, indent=2))

if __name__ == "__main__":
    asyncio.run(get_info())
