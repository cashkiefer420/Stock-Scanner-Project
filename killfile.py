import os
import subprocess
import pwd

def get_user_processes():
    """Get all processes running under the current user"""
    user = pwd.getpwuid(os.getuid()).pw_name
    try:
        result = subprocess.check_output(["ps", "-u", user, "-o", "pid,command"], text=True).strip().split("\n")[1:]
        return [line.strip().split(maxsplit=1) for line in result]
    except subprocess.CalledProcessError as e:
        print(f"Error getting user processes: {e}")
        return []

def kill_processes():
    """Kill all background processes except essential ones"""
    essential_keywords = ["bash", "sshd", "python", "systemd"]  # Exclude essential processes
    processes = get_user_processes()

    if not processes:
        print("No processes found for the current user.")
        return

    for pid, command in processes:
        if any(keyword in command for keyword in essential_keywords):
            print(f"Skipping essential process {pid}: {command}")
            continue
        try:
            os.kill(int(pid), 9)
            print(f"Killed process {pid}: {command}")
        except ProcessLookupError:
            print(f"Process {pid} not found.")
        except PermissionError:
            print(f"Permission denied to kill process {pid}.")
        except Exception as e:
            print(f"Failed to kill {pid}: {e}")

if __name__ == "__main__":
    kill_processes()
