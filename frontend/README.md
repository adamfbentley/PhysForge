# PhysForge Frontend

A modern, professional React frontend for the Physics-Informed Scientific Discovery Platform.

## 🚀 Features

- **Modern React Architecture**: Built with React 18, TypeScript, and modern hooks
- **Professional UI**: Mantine UI components with custom scientific theme
- **State Management**: Zustand for lightweight, scalable state management
- **Authentication**: JWT-based authentication with automatic token refresh
- **Real-time Updates**: Live job monitoring and notifications
- **Responsive Design**: Mobile-first design that works on all devices
- **Accessibility**: WCAG 2.1 compliant components
- **Scientific Visualization**: 3D plotting and equation rendering capabilities

## 🏗️ Architecture

### Tech Stack
- **Framework**: React 18 with TypeScript
- **Routing**: React Router v6
- **State Management**: Zustand
- **UI Library**: Mantine
- **HTTP Client**: Axios with interceptors
- **Forms**: React Hook Form with Zod validation
- **Styling**: Tailwind CSS
- **Icons**: Tabler Icons

### Project Structure
```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── ui/             # Basic UI components
│   │   ├── forms/          # Form components
│   │   ├── layout/         # Layout components
│   │   ├── charts/         # Chart and visualization components
│   │   └── scientific/     # Scientific-specific components
│   ├── pages/              # Page components
│   │   ├── auth/           # Authentication pages
│   │   ├── dashboard/      # Dashboard pages
│   │   ├── datasets/       # Dataset management
│   │   ├── jobs/           # Job management
│   │   ├── results/        # Results visualization
│   │   └── admin/          # Admin panels
│   ├── hooks/              # Custom React hooks
│   ├── services/           # API service functions
│   ├── stores/             # Zustand stores
│   ├── types/              # TypeScript type definitions
│   ├── utils/              # Utility functions
│   ├── constants/          # App constants
│   └── styles/             # Global styles and themes
├── public/                 # Static assets
└── tests/                  # Test files
```

## 🛠️ Setup & Installation

### Prerequisites
- Node.js 18+ and npm
- Backend API running (see backend README)

### Installation

1. **Clone and navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Environment Configuration**
   ```bash
   cp .env.example .env.local
   ```
   Update the environment variables in `.env.local`:
   ```env
   REACT_APP_API_BASE_URL=http://localhost:8000
   REACT_APP_API_GATEWAY_URL=http://localhost:8080
   ```

4. **Start development server**
   ```bash
   npm start
   ```

5. **Build for production**
   ```bash
   npm run build
   ```

## 📋 Available Scripts

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App
- `npm run tailwind` - Watch Tailwind CSS changes

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REACT_APP_API_BASE_URL` | Backend API base URL | `http://localhost:8000` |
| `REACT_APP_API_GATEWAY_URL` | API Gateway URL | `http://localhost:8080` |
| `REACT_APP_NAME` | Application name | `PhysForge` |
| `REACT_APP_ENVIRONMENT` | Environment (development/production) | `development` |

### Theme Customization

The application uses Mantine theme system. Customize colors, fonts, and other theme properties in `src/App.tsx`:

```tsx
<MantineProvider
  theme={{
    colors: {
      brand: ['#e3f2fd', '#bbdefb', '#90caf9', '#64b5f6', '#42a5f5', '#2196f3', '#1e88e5', '#1976d2', '#1565c0', '#0d47a1'],
    },
    primaryColor: 'brand',
  }}
  // ...
>
```

## 🚦 Usage

### Authentication
Users can register and login through the authentication pages. JWT tokens are automatically managed and refreshed.

### Dashboard
The main dashboard provides an overview of:
- Recent jobs and their status
- Dataset statistics
- Quick action buttons for common tasks
- System health indicators

### Dataset Management
- Upload scientific datasets (HDF5, CSV, JSON, NumPy)
- Browse and search datasets
- Preview data with interactive tables
- Download datasets
- Manage metadata and tags

### Job Management
- Create jobs for different types:
  - PINN Training
  - PDE Discovery
  - Derivative Computation
  - Active Experiment Design
- Monitor job progress in real-time
- View job logs and results
- Cancel or retry failed jobs

### Results Visualization
- 3D surface plots for PINN solutions
- Interactive charts for training metrics
- LaTeX equation rendering for discovered PDEs
- Contour plots and heatmaps

## 🔌 API Integration

The frontend communicates with the backend through a structured API service layer:

```typescript
import { apiService } from '../services/api';

// Example: Submit a PINN training job
const submitPinnJob = async (config: PinnJobConfig) => {
  const response = await apiService.post('/jobs/pinn-training', config);
  return response.data;
};
```

## 🧪 Testing

### Unit Tests
```bash
npm test
```

### E2E Tests (Future)
```bash
npm run test:e2e
```

## 📱 Mobile Support

The application is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile phones
- Touch devices

## ♿ Accessibility

- WCAG 2.1 AA compliance
- Screen reader support
- Keyboard navigation
- High contrast mode support
- Focus management

## 🔒 Security

- JWT token-based authentication
- Automatic token refresh
- Secure API communication
- Input validation and sanitization
- XSS protection

## 🚀 Deployment

### Development
```bash
npm start
```

### Production Build
```bash
npm run build
```

### Docker (Future)
```bash
docker build -t physforge-frontend .
docker run -p 3000:80 physforge-frontend
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Contact the development team

## 📊 Performance

- Lazy loading of components
- Code splitting
- Optimized bundle size
- Efficient re-renders with React.memo
- Caching strategies for API calls

## 🔮 Future Enhancements

- [ ] Real-time collaboration features
- [ ] Advanced 3D visualization with Three.js
- [ ] Jupyter notebook integration
- [ ] Offline support with service workers
- [ ] Progressive Web App features
- [ ] Advanced analytics and reporting
- [ ] Plugin system for custom job types
- [ ] Multi-language support (i18n)