# Personal Blog - Frontend

Vue 3 based frontend for the Personal Blog application.

## Features

- User authentication (login/register)
- User profile management
- Article browsing and management
- Responsive design
- Modern UI with Element Plus and Tailwind CSS

## Technology Stack

- Vue 3 (Composition API)
- TypeScript
- Pinia (State Management)
- Vue Router
- Axios (HTTP Client)
- Element Plus (UI Component Library)
- Tailwind CSS (Utility-first CSS Framework)

## Project Structure

```
frontend/
├── src/
│   ├── api/           # API service modules
│   ├── assets/        # Static assets (images, styles)
│   ├── components/    # Reusable Vue components
│   ├── composables/   # Vue composables
│   ├── router/        # Vue Router configuration
│   ├── stores/        # Pinia stores
│   ├── types/         # TypeScript type definitions
│   ├── utils/         # Utility functions
│   ├── views/         # Page components
│   ├── App.vue        # Root component
│   └── main.ts        # Application entry point
├── public/            # Public static files
└── package.json       # Dependencies and scripts
```

## Getting Started

### Prerequisites

- Node.js (version 16 or higher)
- npm or yarn

### Installation

1. Clone the repository
2. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
3. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   ```

### Development

Start the development server:

```bash
npm run dev
# or
yarn dev
```

The application will be available at `http://localhost:3000`.

### Building for Production

```bash
npm run build
# or
yarn build
```

The built files will be in the `dist` directory.

## API Integration

The frontend communicates with the backend API running at `http://localhost:8080` by default. Proxy configuration is set up in `vite.config.ts`.

### Available Endpoints

- `POST /user/account/login` - User login
- `POST /user/account/register` - User registration
- `GET /user/account/info` - Get user information

## Environment Variables

- `VITE_API_BASE_URL` - Base URL for API requests (default: `http://localhost:8080`)

## Authentication Flow

1. User logs in with username/password
2. Backend returns JWT token
3. Token is stored in localStorage
4. Subsequent requests include token in Authorization header
5. Token is validated on protected routes

## Contributing

1. Follow the existing code style
2. Write meaningful commit messages
3. Add tests for new features
4. Update documentation as needed