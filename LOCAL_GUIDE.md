# Local operation guide 

## 🐳 Docker One click start (recommend)

Just need **git clone** Then execute a command to start：

```bash
git clone <your-repo-url>
cd ai-goofish-monitor
cp .env.example .env
cp config.json.example config.json
docker compose up -d
```

- Access address：`http://127.0.0.1:8000`
- Default account/The password is the same as the description below

### development mode (Optional)

If you want to develop front-end or back-end code, use the development version compose：

```bash
docker compose -f docker-compose.dev.yaml up -d --build
```

## 🛠️ Manual installation steps 

### Step One: Environment Preparation (rear end Python)

1.  **Clone the project and go into the directory**：
    ```bash
    git clone <your-repo-url>
    cd ai-goofish-monitor
    ```

2.  **Create and activate a virtual environment** (recommend)：
    - **Linux/macOS**:
      ```bash
      python3 -m venv .venv
      source .venv/bin/activate
      ```
    - **Windows**:
      ```bash
      python -m venv .venv
      .venv\Scripts\activate
      ```

3.  **Install Python rely**：
    ```bash
    pip install -r requirements.txt
    ```

4.  **Browser preparation**：
    This project passes by default when running locally `channel="chrome"` Call the one installed on your system **Google Chrome** or **Microsoft Edge**。
    
    - Please make sure your computer has one of these installed。
    - **No need** run `playwright install` Download additional browser kernels。

### Step 2: Compile the front end (Vue3 + Shadcn UI)

The project adopts a front-end and back-end separation architecture, and the front-end code needs to be compiled and packaged first.，The backend can provide normal Web interface。

1.  **Enter the front-end directory**：
    
    ```bash
    cd web-ui
    ```
    
2.  **Install Node.js rely**：
    ```bash
    npm install
    ```

3.  **Execute build packaging**：
    
    ```bash
    npm run build
    ```
    
4.  **Move build artifacts to a location accessible on the backend**：
    - **Linux/macOS**:
      ```bash
      rm -rf ../dist && mv dist ../
      ```
    - **Windows (PowerShell)**:
      ```powershell
      Remove-Item -Recurse -Force ..\dist; Move-Item dist ..\
      ```

5.  **Return to root directory**：
    ```bash
    cd ..
    ```

### Step 3: Configuration file

1.  **create `.env` document**：
    ```bash
    cp .env.example .env
    ```
    edit `.env` file, fill in at least `OPENAI_API_KEY`。If you have no specific model needs, it is recommended to keep `OPENAI_BASE_URL` as default or use your reliable proxy address。

2.  **create `config.json` document** (Task configuration)：
    
    ```bash
    cp config.json.example config.json
    ```

### Step 4: Start the service

Run in the project root directory and ensure that the virtual environment is activated：

```bash
python web_server.py
```

- **Default address**：`http://127.0.0.1:8000`
- **Default account**：`admin`
- **default password**：`admin123` (Available at `.env` pass `WEB_USERNAME` and `WEB_PASSWORD` Revise)

## 
