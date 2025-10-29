module.exports = {
  apps: [{
      name: "demo-rsi",
      interpreter: "./venv/bin/python3",
      script: "uvicorn",
        args: "main:app --host 10.9.23.2 --port 8123",
        watch: true,
        exec_mode: "fork",          
    },
  ]
}
