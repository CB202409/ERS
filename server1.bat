cd .\react

REM Check if node_modules folder exists
IF NOT EXIST node_modules (
    echo Installing dependencies...
    npm install
)

echo Starting the application...
npm run start