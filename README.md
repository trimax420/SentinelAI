# 🛡️ Security CV Dashboard

<div align="center">

![Security Dashboard](https://img.shields.io/badge/Security-Dashboard-blue?style=for-the-badge&logo=shield)
![AI Powered](https://img.shields.io/badge/AI-Powered-green?style=for-the-badge&logo=brain)
![Real Time](https://img.shields.io/badge/Real--Time-Monitoring-red?style=for-the-badge&logo=video)

**A comprehensive AI-powered security surveillance and monitoring system that combines computer vision, real-time analytics, and an intuitive web dashboard for enhanced security management.**

---

</div>

## ✨ Key Highlights

> 🔥 **Real-time AI Detection** | 🎯 **Advanced Analytics** | ☁️ **Cloud Integration** | 📱 **Modern Dashboard**

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

### ☁️ **Cloud Integration & Data Logging**
- 🗄️ **AWS S3 Storage**: Secure cloud storage for snapshots, videos, and evidence
- 📝 **Cloud Data Logging**: Comprehensive logging of all security events and analytics
- 🔄 **Real-time Sync**: Automatic synchronization of data to cloud storage
- 📊 **Cloud Analytics**: Historical data analysis and reporting in the cloud
- 🔐 **Secure Backup**: Encrypted backup of all security data and configurations
- 📱 **Remote Access**: Access logs and data from anywhere with cloud integration
- 🔍 **Audit Trail**: Complete audit trail of all system activities stored in cloud
- 📈 **Scalable Storage**: Auto-scaling cloud storage for growing data needs

## 🏗️ Architecture

### Backend (FastAPI + Python)
- **FastAPI**: High-performance REST API
- **Computer Vision**: OpenCV, YOLO, MediaPipe, face_recognition
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Real-time Processing**: WebSocket connections for live updates
- **Cloud Storage**: AWS S3 integration for media storage

### Frontend (Next.js + React)
- **Next.js 14**: Modern React framework with TypeScript
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Accessible component library
- **Recharts**: Interactive data visualization
- **Real-time Updates**: Live data synchronization

## 📋 Prerequisites

- **Python 3.8+**
- **Node.js 18+**
- **PostgreSQL 12+**
- **FFmpeg** (for video processing)
- **CUDA** (optional, for GPU acceleration)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd security-cv-dashboard
```

### 2. Backend Setup

#### Create Virtual Environment
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Environment Configuration
Create a `.env` file in the backend directory:
```env
# Database
DATABASE_URL=postgresql://username:password@localhost/security_db

# API Configuration
PROJECT_NAME=Security Monitoring System
VERSION=1.0.0
DESCRIPTION=AI-powered security surveillance system
CORS_ORIGINS=["http://localhost:3000"]

# Storage
SNAPSHOT_BASE_DIR=data/snapshots

# AWS S3 (Optional)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name

# Camera Configuration
DEFAULT_RTSP_URL=rtsp://your-camera-url
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

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`

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
