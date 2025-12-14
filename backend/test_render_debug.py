#!/usr/bin/env python3
"""
Debug script to test rendering and capture detailed logs
"""
import sys
import requests
import time
import json

API_BASE = "http://localhost:8000"

def main():
    # Create project
    print("1. Creating project...")
    project_resp = requests.post(
        f"{API_BASE}/api/projects",
        json={"name": "Debug Test Video", "description": "Testing render with debug"}
    )
    project_resp.raise_for_status()
    project = project_resp.json()
    project_id = project['id']
    print(f"   ✓ Project created: {project_id}")
    
    # Create scene
    print("2. Creating scene...")
    scene_resp = requests.post(
        f"{API_BASE}/api/scenes",
        json={
            "project_id": project_id,
            "number": 1,
            "prompt": "A person walking through a beautiful city at sunset, cinematic wide shot, golden hour lighting"
        }
    )
    scene_resp.raise_for_status()
    scene = scene_resp.json()
    scene_id = scene['id']
    print(f"   ✓ Scene created: {scene_id}")
    
    # Start render
    print("3. Starting render...")
    render_resp = requests.post(
        f"{API_BASE}/api/render/scenes/{scene_id}/render",
        params={"project_id": project_id}
    )
    render_resp.raise_for_status()
    render_result = render_resp.json()
    task_id = render_result['task_id']
    print(f"   ✓ Render started: task_id={task_id}")
    
    # Monitor progress
    print("4. Monitoring render progress...")
    print("   (This may take 2-5 minutes)")
    
    max_wait = 600  # 10 minutes
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < max_wait:
        # Check task status
        task_resp = requests.get(f"{API_BASE}/api/render/tasks/{task_id}")
        task_resp.raise_for_status()
        task_status = task_resp.json()
        
        current_status = task_status.get('status')
        if current_status != last_status:
            print(f"   Status: {current_status}")
            last_status = current_status
        
        if current_status == 'SUCCESS':
            result = task_status.get('result', {})
            if result.get('success'):
                print(f"\n✅ SUCCESS! Video created!")
                print(f"   Video path: {result.get('video_path')}")
                return True
            else:
                error = result.get('error', 'Unknown error')
                print(f"\n❌ Render failed: {error}")
                return False
        
        if current_status == 'FAILURE':
            print(f"\n❌ Task failed")
            info = task_status.get('info', {})
            print(f"   Info: {info}")
            return False
        
        # Check scene status
        scenes_resp = requests.get(f"{API_BASE}/api/scenes", params={"project_id": project_id})
        scenes_resp.raise_for_status()
        scenes = scenes_resp.json()
        scene = next((s for s in scenes if s['id'] == scene_id), None)
        
        if scene:
            scene_status = scene.get('status')
            if scene_status != last_status:
                print(f"   Scene status: {scene_status}")
                if scene_status == 'completed':
                    print(f"\n✅ Scene completed!")
                    print(f"   Video path: {scene.get('video_path')}")
                    return True
                elif scene_status == 'failed':
                    error = scene.get('error', 'Unknown error')
                    print(f"\n❌ Scene failed: {error}")
                    return False
        
        time.sleep(5)
    
    print(f"\n⏱️  Timeout after {max_wait} seconds")
    return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

