import os
import subprocess
import sys
import importlib.util


def is_package_installed(package_name):
    """
    특정 패키지가 설치되어 있는지 확인합니다.
    """
    return importlib.util.find_spec(package_name) is not None


def install_package(package_name):
    """
    특정 패키지를 설치합니다.
    """
    try:
        print(f"패키지 {package_name} 설치 중...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"{package_name} 설치 완료.")
    except subprocess.CalledProcessError as e:
        print(f"{package_name} 설치 중 오류 발생: {e}")
        sys.exit(1)


def install_requirements():
    """
    requirements.txt 파일의 모든 패키지를 설치합니다.
    """
    requirements_path = os.path.join(os.path.dirname(__file__), "../requirements.txt")
    print(f"requirements.txt 경로: {requirements_path}")
    try:
        print("requirements.txt에 정의된 모든 패키지를 설치 중입니다...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
        print("requirements.txt의 모든 패키지가 설치되었습니다.")
    except subprocess.CalledProcessError as e:
        print(f"requirements.txt 설치 중 오류 발생: {e}")
        sys.exit(1)


def parse_requirements():
    """
    requirements.txt에서 패키지 목록을 읽습니다.
    """
    requirements_path = os.path.join(os.path.dirname(__file__), "../requirements.txt")
    required_packages = []
    try:
        with open(requirements_path, "r") as file:
            for line in file:
                # 코멘트와 빈 줄 제외
                line = line.strip()
                if line and not line.startswith("#"):
                    required_packages.append(line)
    except FileNotFoundError:
        print("requirements.txt 파일이 존재하지 않습니다.")
        sys.exit(1)
    return required_packages


def check_and_install_packages():
    """
    requirements.txt에 있는 모든 패키지를 확인하고 없으면 설치합니다.
    """
    required_packages = parse_requirements()
    print("확인할 패키지 목록:", required_packages)

    for package in required_packages:
        # Git 패키지 확인
        if package.startswith("git+"):
            package_name = package.split("/")[-1].split(".git")[0]
            if not is_package_installed(package_name):
                print(f"{package_name} 패키지가 설치되어 있지 않습니다. 설치를 시작합니다.")
                install_package(package)
        else:
            package_name = package.split("==")[0] if "==" in package else package
            if not is_package_installed(package_name):
                print(f"{package_name} 패키지가 설치되어 있지 않습니다. 설치를 시작합니다.")
                install_package(package_name)
            else:
                print(f"{package_name} 패키지가 이미 설치되어 있습니다.")
