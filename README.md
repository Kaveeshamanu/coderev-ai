**User Guide**

A.1 System Requirements

The following minimum platform specification is required to run the CodeRev AI system:

•	Node.js version 18 or higher (for the frontend development server)

•	Python 3.8 or higher (for the backend server)

•	8 GB RAM minimum (16 GB recommended for model inference)

•	A modern web browser (Chrome, Firefox, Edge, or Safari)

•	A network connection between the frontend and backend servers (localhost for local deployment)

A.2 Installation

To install and run the frontend web application, navigate to the project frontend directory and execute the following commands in a terminal:

npm install

npm run dev

The application will be available at http://localhost:5173 (or the next available port if 5173 is in use).
To install and run the backend server, navigate to the backend directory, activate the Python virtual environment, and execute:

pip install -r requirements.txt

uvicorn main:app --reload --port 8000

A.3 Usage

Upon opening the web application in a browser, users are presented with a login screen. After authenticating, the Dashboard provides an overview of review statistics and recent activity. To use the Contributor Mode, navigate to the Contributor Workspace, paste a Java method into the code editor, optionally adjust the beam size setting, and click "Run AI Review". Ranked suggestions will appear below the editor. To use the Reviewer Mode, navigate to the Reviewer Workspace, provide both a Java method and a natural language reviewer comment, and click "Implement Review Comment". Generated implementations will be displayed in a grid with confidence scores. Review history is accessible from the History page via the sidebar navigation.
