# PERERIA

<div style="display: flex; align-items: center;">
  <img src="https://github.com/AbhayGRT/POATAN/blob/main/Unnecessary/ufc-mma.gif" width="200" height="200" />
  <img src="https://github.com/AbhayGRT/POATAN/raw/main/Unnecessary/poatan.png" width="600" height="200" style="margin-right: 10px;" />
  <img src="https://github.com/AbhayGRT/POATAN/raw/main/Unnecessary/alex-pereira.gif" width="200" height="200" />
</div>


## Prerequisites
Ensure you have Python installed on your system. You also need access to an `.env` file with the necessary credentials.

## Getting Started

### 1. Download the Virtual Environment
First, download the virtual environment setup for this project from the following link:
[Download Virtual Environment](https://drive.google.com/file/d/1kKL8TazOd1CpiOi3HXa8sgP9K20vd7Ul/view?usp=sharing)

### 2. Set Up the Virtual Environment
Navigate to the project directory and activate the virtual environment.

**For Linux/macOS:**
```bash
cd grafanalabs
source bin/activate
```
**Execute the code**
```bash
python main.py
```

### 3. Customization
If you want to customize the following, modify the `localMetaInfo.json` file:
- **Client settings**: Specify which clients you want to monitor.
- **Duration**: Set the duration for data scraping.
- **Output folder name**: Customize the name of the folder for saving Excel files.
- **S3 bucket name**: Define your custom S3 bucket for data storage.

