#!/bin/bash

# Capture the current working directory
WORKING_DIR=$(pwd)

# Check OS type
if [ -f /etc/debian_version ]; then
    OS_FAMILY="debian"
elif [ -f /etc/redhat-release ]; then
    OS_FAMILY="rhel"
elif [ -f /etc/arch-release ]; then
    OS_FAMILY="arch"
else
    echo "Unsupported Linux distribution"
    exit 1
fi

# Set icon path
ICON_PATH="img/ai-garage.png"

# Set main script path
MAIN_SCRIPT="launch.sh"

# Check for required packages and install if missing
if [ "$OS_FAMILY" = "debian" ]; then
    PKG_MANAGER="apt-get"
    REQUIRED_PKGS="lm-sensors python3 python3-pip python3-pyqt6 python3-pyqt6-webengine qtwebengine mesa qt6-base"
elif [ "$OS_FAMILY" = "rhel" ]; then
    PKG_MANAGER="dnf"
    REQUIRED_PKGS="lm_sensors python3 python3-pip python3-qt6 python3-qt6-webengine qt-webengine mesa-libGL qt6-base"
elif [ "$OS_FAMILY" = "arch" ]; then
    PKG_MANAGER="pacman"
    REQUIRED_PKGS="lm_sensors python python-pip python-pyqt6 python-pyqt6-webengine qt-webengine mesa qt6-base"
fi

for pkg in $REQUIRED_PKGS; do
    if ! $PKG_MANAGER list installed | grep -q "^$pkg"; then
        if [ "$OS_FAMILY" = "arch" ]; then
            sudo pacman -Sy --needed $pkg
        else
            sudo $PKG_MANAGER install -y $pkg
        fi
    fi
done

# Check for conda
if ! command -v conda &> /dev/null; then
    echo "Conda not found, installing Miniconda..."
    if [ "$OS_FAMILY" = "arch" ]; then
        sudo pacman -Sy --needed miniconda
    else
        wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
        bash miniconda.sh -b -p $HOME/miniconda
        rm miniconda.sh
        export PATH="$HOME/miniconda/bin:$PATH"
    fi
fi

# Create conda environment
echo "Creating conda environment..."
conda create -y -n AI-Garage python=3.12
conda activate AI-Garage
conda install -c conda-forge pip pyqt pyqtwebengine psutil pynvml numpy pandas matplotlib configparser requests beautifulsoup4 jsonschema pycryptodome


# Install Python dependencies using pip
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create the launch script
echo "#!/bin/bash" > $MAIN_SCRIPT
echo "conda activate AI-Garage" >> $MAIN_SCRIPT
echo "python3 $WORKING_DIR/main.py" >> $MAIN_SCRIPT

# Make the launch script executable
chmod +x $MAIN_SCRIPT

# Create desktop launcher
LAUNCHER_FILE="ai-garage.desktop"
echo "[Desktop Entry]" > $LAUNCHER_FILE
echo "Version=1.1.0" >> $LAUNCHER_FILE
echo "Type=Application" >> $LAUNCHER_FILE
echo "Name=AI Garage" >> $LAUNCHER_FILE
echo "Comment=Created by Captain ASIC" >> $LAUNCHER_FILE
echo "Exec=$WORKING_DIR/$MAIN_SCRIPT" >> $LAUNCHER_FILE
echo "Icon=/usr/share/icons/ai-garage.png" >> $LAUNCHER_FILE
echo "Terminal=false" >> $LAUNCHER_FILE
echo "Categories=Development;" >> $LAUNCHER_FILE

# Move icon to a standard location
sudo mkdir -p /usr/share/icons/
sudo cp $ICON_PATH /usr/share/icons/ai-garage.png

# Make launcher executable
chmod +x $LAUNCHER_FILE

# Move launcher to desktop directory
sudo mv $LAUNCHER_FILE /usr/share/applications/

echo "Setup complete. You can now launch AI Garage from your applications menu."
