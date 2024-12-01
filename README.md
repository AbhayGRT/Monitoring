# POATAN

![Poatan Image](https://github.com/AbhayGRT/POATAN/blob/main/poatan.png)
![Alex Pereria](https://media.tenor.com/images/64a0d8103fd8286ed7f78db299aafc16/tenor.gif)

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

