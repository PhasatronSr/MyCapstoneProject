# MyCapstoneProject

---

## 🛠 Built With

* **Python** (3.13.2)
* **Streamlit** - Web framework
* **OpenCV & MediaPipe** - Computer Vision
* **Pandas** - Data manipulation
* **Matplotlib, Plotly & Altair** - Data visualization

---

## 🚀 Getting Started

Follow these instructions to set up the project on your local machine.

### Prerequisites

Before you begin, ensure you have the following installed:

* **Python 3.13.2** — [Download here](https://www.python.org/downloads/)

---

### 1. Clone the Repository

Clone this repository to your local machine and navigate into the folder:

```bash
git clone https://github.com/your-username/MyCapstoneProject.git
cd MyCapstoneProject
```

---

### 2. Create a Virtual Environment *(Optional)*

It is recommended to use a virtual environment to keep dependencies isolated, but this step is optional.

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

---

### 3. Install Dependencies

Install all required packages using `pip`:

```bash
pip install -r requirements.txt
```

If you don't have a `requirements.txt` yet, you can install the packages manually:

```bash
pip install streamlit==1.54.0 pandas==2.3.3 matplotlib==3.10.8 mediapipe==0.10.9 opencv-contrib-python==4.13.0.92 plotly==6.6.0 altair==6.0.0
```

---

### 4. Run the Application

Start the Streamlit app with the following command:

```bash
streamlit run UI.py
```

Once running, open your browser and go to:

```
http://localhost:8501
```

---


## 📦 Requirements

| Package      | Purpose                  |
|--------------|--------------------------|
| Streamlit    | Web framework / UI       |
| OpenCV       | Computer vision          |
| MediaPipe    | Pose / hand detection    |
| Pandas       | Data manipulation        |
| Matplotlib   | Static data visualization|
| Plotly       | Interactive charts       |
| Altair       | Declarative charts       |

---

## 🙋 Troubleshooting

- **`ModuleNotFoundError`** — Make sure your virtual environment is activated and all dependencies are installed.
- **Camera not found (OpenCV)** — Ensure your webcam is connected and not in use by another application.
- **Streamlit not found** — Run `pip install streamlit` inside your activated virtual environment.

---

## 📄 License

This project was developed for **academic purposes** as part of a capstone project. All rights reserved by the author. Not intended for commercial use.
