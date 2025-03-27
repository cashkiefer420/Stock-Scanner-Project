
import os
import subprocess

def get_user_processes():
    """Get all processes running under the current user"""
    user = os.getlogin()
    try:
        result = subprocess.check_output(["ps", "-u", user, "-o", "pid,command"], text=True).strip().split("\n")[1:]
        return [line.strip().split(maxsplit=1) for line in result]
    except subprocess.CalledProcessError:
        return []

def kill_processes():
    """Kill all background processes except essential ones"""
    essential_keywords = ["bash", "sshd", "python", "systemd"]  # Exclude essential processes
    processes = get_user_processes()

    for pid, command in processes:
        if any(keyword in command for keyword in essential_keywords):
            continue
        try:
            os.kill(int(pid), 9)
            print(f"Killed process {pid}: {command}")
        except Exception as e:
            print(f"Failed to kill {pid}: {e}")

if __name__ == "__main__":
    kill_processes()