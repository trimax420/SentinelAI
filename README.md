# 🚨 SentinelAI

<div align="center">

![SentinelAI](https://img.shields.io/badge/SentinelAI-Security%20Platform-blue?style=for-the-badge&logo=shield)
![AI Powered](https://img.shields.io/badge/AI-Powered-green?style=for-the-badge&logo=brain)
![Real Time](https://img.shields.io/badge/Real--Time-Monitoring-red?style=for-the-badge&logo=video)
![Hybrid Cloud](https://img.shields.io/badge/Hybrid-Cloud-orange?style=for-the-badge&logo=cloud)

**🤖 Your Digital Guardian Never Sleeps**

*A comprehensive AI-powered security surveillance platform that combines on-premises computer vision processing with cloud-based dashboard and data logging for optimal performance and scalability.*

---

</div>

## ✨ Key Highlights

> 🔥 **On-Premises AI Processing** | 🎯 **Cloud Dashboard** | ☁️ **Hybrid Architecture** | 📊 **Cloud Data Logging**

## 🏗️ **Hybrid Deployment Architecture**

<div align="center">

```
🏢 ON-PREMISES                    ☁️ CLOUD
┌─────────────────────┐          ┌─────────────────────┐
│  🎥 Camera Feeds    │          │  📱 Web Dashboard   │
│  🧠 AI Processing   │ ────────▶│  📊 Analytics UI    │
│  🔍 Detection       │          │  ⚠️  Alert Panel    │
│  📸 Evidence        │          │  👥 User Management │
└─────────────────────┘          └─────────────────────┘
         │                                │
         ▼                                ▼
┌─────────────────────┐          ┌─────────────────────┐
│  🗄️ Local Storage   │ ────────▶│  📝 Cloud Logging   │
│  ⚡ Real-time Data  │          │  🔄 Data Sync       │
│  🔐 Secure Backup  │          │  📈 Long-term Data  │
└─────────────────────┘          └─────────────────────┘
```

**🎯 Best of Both Worlds:** *Secure on-premises processing with cloud accessibility*

</div>

## 🚀 Core Features

### 🎥 **Video Surveillance & Detection**
- 📹 **Real-time Video Surveillance**: Live camera feeds with RTSP support
- 🤖 **AI-Powered Person Detection**: YOLO-based object detection for accurate person tracking
- 👤 **Facial Recognition**: Advanced suspect identification and tracking system
- 🕺 **Behavior Analysis**: Suspicious activity detection using MediaPipe pose estimation
- 🗺️ **Zone-based Analytics**: Customizable monitoring zones with occupancy tracking
- 🚨 **Real-time Alerts**: Instant notifications for security incidents

### 📊 **Dashboard & Analytics**
- 🖥️ **Live Camera Management**: Monitor multiple camera feeds simultaneously
- 📈 **Interactive Analytics**: Real-time metrics, charts, and heatmaps
- ⚠️ **Alert Management**: Comprehensive alert system with severity levels
- 🔍 **Suspect Database**: Maintain and manage suspect profiles with images
- 👥 **Demographics Analysis**: Age and gender detection for visitor insights
- 🏪 **Store Mapping**: Visual representation of camera locations and zones

### 🔧 **Advanced Security Features**
- ⏰ **Loitering Detection**: Identify persons staying in areas for extended periods
- 🚫 **Restricted Area Monitoring**: Alert when unauthorized access is detected
- 📍 **Dwell Time Analysis**: Track how long people spend in specific zones
- 🚶 **Traffic Pattern Analysis**: Understand visitor flow and peak hours
- 📸 **Evidence Management**: Automated snapshot capture for incidents

### 🏢 **On-Premises Processing**
- 🧠 **Local AI Processing**: All computer vision and detection runs on-premises for privacy
- ⚡ **Real-time Analysis**: Instant processing without cloud latency
- 🔐 **Data Privacy**: Sensitive video data never leaves your premises
- 💾 **Local Storage**: Critical evidence stored locally for immediate access
- 🚀 **High Performance**: Dedicated hardware for optimal processing speed
- 🔒 **Secure Environment**: Complete control over your security infrastructure

### ☁️ **Cloud Dashboard & Logging**
- 📱 **Cloud Dashboard**: Access your security interface from anywhere
- 📊 **Cloud Analytics**: Historical data analysis and reporting in the cloud
- 📝 **Comprehensive Logging**: All events, alerts, and analytics logged to cloud
- 🔄 **Real-time Sync**: Metadata and analytics synchronized to cloud
- 🌐 **Remote Access**: Monitor your system from any location
- 📈 **Scalable Storage**: Auto-scaling cloud storage for logs and analytics
- 🔍 **Audit Trail**: Complete audit trail of all system activities
- 🔐 **Encrypted Backup**: Secure backup of configurations and non-sensitive data

## 🏗️ **SentinelAI Technical Architecture**

<div align="center">

### 🔄 **Hybrid Cloud Architecture**

```
🏢 ON-PREMISES PROCESSING           ☁️ CLOUD SERVICES
┌─────────────────────────────┐    ┌─────────────────────────────┐
│  🎥 RTSP Camera Feeds       │    │  📱 Web Dashboard           │
│  ├─ Live Video Streams      │    │  ├─ Real-time Monitoring    │
│  └─ Multi-camera Support    │    │  └─ Alert Management        │
└─────────────────────────────┘    └─────────────────────────────┘
              │                                    ▲
              ▼                                    │
┌─────────────────────────────┐                   │
│  🧠 AI Processing Engine    │                   │
│  ├─ YOLO Object Detection   │                   │
│  ├─ Facial Recognition      │                   │
│  ├─ Behavior Analysis       │                   │
│  └─ Zone Analytics          │                   │
└─────────────────────────────┘                   │
              │                                    │
              ▼                                    │
┌─────────────────────────────┐    ┌─────────────────────────────┐
│  🚀 FastAPI Backend         │────│  📊 Cloud Analytics         │
│  ├─ Real-time API           │    │  ├─ Historical Data         │
│  ├─ WebSocket Streams       │    │  ├─ Trend Analysis          │
│  └─ Alert Generation        │    │  └─ Reporting Engine        │
└─────────────────────────────┘    └─────────────────────────────┘
              │                                    │
              ▼                                    ▼
┌─────────────────────────────┐    ┌─────────────────────────────┐
│  💾 Local Storage           │────│  📝 Cloud Logging           │
│  ├─ Video Evidence          │    │  ├─ Event Logs              │
│  ├─ Snapshots              │    │  ├─ Analytics Data           │
│  └─ Configuration           │    │  └─ Audit Trail             │
└─────────────────────────────┘    └─────────────────────────────┘
```

</div>

### 🏢 **On-Premises Stack** (Privacy-First Processing)
- 🚀 **FastAPI**: High-performance REST API with automatic documentation
- 👁️ **Computer Vision**: OpenCV, YOLO, MediaPipe, face_recognition
- 🗃️ **Local Database**: PostgreSQL with SQLAlchemy ORM for local data
- ⚡ **Real-time Processing**: WebSocket connections for live updates
- 🧠 **AI Engine**: Local processing ensures data privacy and low latency
- 📊 **Analytics Engine**: Real-time data processing and insights
- 🔐 **Security**: JWT authentication and role-based access control

### ☁️ **Cloud Stack** (Dashboard & Logging)
- ⚛️ **Next.js 14**: Modern React framework with TypeScript support
- 🎨 **Tailwind CSS**: Utility-first CSS framework for rapid UI development
- 🧩 **Radix UI**: Accessible, unstyled component library
- 📊 **Recharts**: Interactive data visualization and charting
- 🔄 **Real-time Updates**: Live data synchronization with WebSockets
- 📱 **Responsive Design**: Mobile-first responsive interface
- ☁️ **Cloud Services**: AWS/Azure integration for logging and storage

## 📋 Prerequisites

<div align="center">

| Component | Version | Purpose | Deployment |
|-----------|---------|---------|------------|
| 🐍 **Python** | 3.8+ | Backend API & AI processing | On-Premises |
| 🟢 **Node.js** | 18+ | Frontend development | Cloud |
| 🐘 **PostgreSQL** | 12+ | Database management | On-Premises |
| 🎬 **FFmpeg** | Latest | Video processing | On-Premises |
| 🚀 **CUDA** | Optional | GPU acceleration | On-Premises |
| ☁️ **Cloud Account** | Required | Dashboard & logging | Cloud |

</div>

## 🛠️ **SentinelAI Installation Guide**

### 🔥 **Step 1: Clone Repository**
```bash
git clone <repository-url>
cd SentinelAI
```

### 🐍 **Step 2: Backend Setup**

<details>
<summary>🔧 <strong>Backend Configuration</strong> (Click to expand)</summary>

#### Create Virtual Environment
```bash
cd backend
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Environment Configuration
Create a `.env` file in the backend directory:

```env
# 🗃️ Database Configuration
DATABASE_URL=postgresql://username:password@localhost/security_db

# 🚀 API Configuration
PROJECT_NAME=SentinelAI
VERSION=1.0.0
DESCRIPTION=Your Digital Guardian Never Sleeps
CORS_ORIGINS=["http://localhost:3000", "https://your-cloud-dashboard.com"]

# 📁 Local Storage
SNAPSHOT_BASE_DIR=data/snapshots

# ☁️ AWS S3 Cloud Storage & Logging
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-security-bucket

# 📝 Cloud Logging Configuration
ENABLE_CLOUD_LOGGING=true
LOG_RETENTION_DAYS=90
CLOUD_LOG_LEVEL=INFO

# 📹 Camera Configuration
DEFAULT_RTSP_URL=rtsp://your-camera-url
MAX_CAMERAS=10
DETECTION_CONFIDENCE=0.5
```

#### Database Setup
```bash
# Run migrations
python -m alembic upgrade head

# Or use the migration scripts
python run_migrations.py
```

#### Start Backend Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

✅ **Backend running at:** `http://localhost:8000`

</details>

### ☁️ **Step 3: Cloud Dashboard Setup**

<details>
<summary>🎨 <strong>Cloud Dashboard Configuration</strong> (Click to expand)</summary>

```bash
cd frontend
npm install

# Configure environment for cloud deployment
cp .env.example .env.production
# Edit .env.production with your cloud settings

# For development
npm run dev

# For cloud deployment
npm run build
npm run start
```

✅ **Dashboard accessible at:** `https://your-cloud-domain.com`

</details>

### 🔄 **Step 4: Hybrid Connection Setup**

<details>
<summary>🌐 <strong>Connect On-Premises to Cloud</strong> (Click to expand)</summary>

```bash
# Configure secure connection between on-premises and cloud
# Set up VPN or secure tunnel if required

# Update backend configuration for cloud connectivity
CLOUD_DASHBOARD_URL=https://your-cloud-dashboard.com
CLOUD_LOGGING_ENDPOINT=https://api.your-cloud.com/logs
API_KEY=your-secure-api-key
```

</details>

### 🚀 **Quick Setup Script**
```bash
# Use the automated setup script
chmod +x setup.sh
./setup.sh --hybrid-mode
```

## 🎯 Usage

### Camera Configuration
1. Navigate to the **Cameras** section
2. Add your RTSP camera URLs
3. Configure monitoring zones for each camera
4. Set detection parameters and alert thresholds

### Suspect Management
1. Go to the **Suspects** section
2. Upload suspect photos for facial recognition
3. The system will automatically detect and alert when suspects are identified

### Real-time Monitoring
1. Use the **Dashboard** for overview metrics
2. Monitor live feeds in the **Cameras** section
3. Review alerts in the **Alerts** panel
4. Analyze traffic patterns and demographics

### Testing RTSP Feeds
Use the included test utility:
```bash
python test-feed.py rtsp://your-camera-url
```

## 🔧 API Endpoints

### Core Endpoints
- `GET /api/cameras/` - Camera management
- `GET /api/live-cameras/status/` - Live camera status
- `GET /api/analytics/current/` - Real-time analytics
- `GET /api/alerts/` - Alert management
- `GET /api/suspects/` - Suspect database

### WebSocket Endpoints
- `/ws/live-feed/{camera_id}` - Live video stream
- `/ws/alerts` - Real-time alert notifications

## 📊 Analytics Features

### Real-time Metrics
- Active camera count
- Current people detection
- Alert statistics
- Zone occupancy rates

### Historical Analysis
- Hourly/daily traffic patterns
- Demographics breakdown
- Alert trend analysis
- Dwell time statistics

### Visualization
- Interactive charts and graphs
- Heat maps for traffic flow
- Timeline views for alerts
- Store layout mapping

## 🔒 Security Features

### Detection Capabilities
- **Person Detection**: YOLO-based object detection
- **Face Recognition**: Multi-face encoding and matching
- **Pose Analysis**: Suspicious behavior detection
- **Loitering Detection**: Extended presence monitoring

### Alert System
- **Severity Levels**: Critical, high, medium, low
- **Alert Types**: Suspect detected, loitering, restricted access
- **Acknowledgment System**: Track alert responses
- **Real-time Notifications**: Instant WebSocket updates

## 🚀 Deployment

### Docker Deployment (Recommended)
```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Manual Deployment
1. Set up PostgreSQL database
2. Configure environment variables
3. Deploy backend with gunicorn
4. Build and serve frontend with nginx
5. Set up reverse proxy for API routing

## 🔧 Configuration

### Camera Settings
- RTSP URL configuration
- Detection confidence thresholds
- Zone polygon definitions
- Alert sensitivity levels

### Model Configuration
- YOLO model selection (YOLOv5/YOLOv8)
- Face recognition tolerance
- Pose detection parameters
- Behavior analysis thresholds

## 📝 Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## 🧪 Testing

### Test RTSP Connection
```bash
python test-feed.py rtsp://camera-url --timeout 30
```

### API Testing
The FastAPI backend includes automatic API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 📚 Dependencies

### Backend Key Dependencies
- **FastAPI**: Web framework
- **OpenCV**: Computer vision processing
- **YOLO (Ultralytics)**: Object detection
- **face_recognition**: Facial recognition
- **MediaPipe**: Pose estimation
- **SQLAlchemy**: Database ORM
- **boto3**: AWS S3 integration

### Frontend Key Dependencies
- **Next.js**: React framework
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **Radix UI**: Component library
- **Recharts**: Data visualization
- **Axios**: API communication

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the API documentation at `/docs`
- Review the logs in `backend/logs/app.log`
- Test camera connections with `test-feed.py`

## 🔄 Updates

### Recent Features
- Enhanced facial recognition accuracy
- Improved pose-based behavior analysis
- Real-time WebSocket updates
- S3 cloud storage integration
- Demographics analysis with DeepFace

### Roadmap
- Mobile app development
- Advanced AI models integration
- Multi-tenant support
- Enhanced reporting features
- Integration with external security systems

---

**Note**: This system is designed for legitimate security monitoring purposes. Ensure compliance with local privacy laws and regulations when deploying surveillance systems.
