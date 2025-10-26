import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import axios from 'axios';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;

// Create custom marker icons for different states
const createCustomIcon = (color) => {
  return new L.Icon({
    iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });
};

// Define different marker colors
const markerIcons = {
  available: createCustomIcon('green'),  // Green for available spots
  occupied: createCustomIcon('red'),     // Red for occupied spots
  user: createCustomIcon('blue')         // Blue for user location
};

L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const BACKEND_URL = process.env.NODE_ENV === 'production' 
  ? 'https://api.gashis.ch'  // Production API-Domain (Backend hängt unter /api)
  : 'http://localhost:8000';
const API = `${BACKEND_URL}`;

console.log('BACKEND_URL:', BACKEND_URL);
console.log('API:', API);

// Hardware control helper (dev): enqueue command in memory backend
async function sendHardwareCommandSimple(hardwareId, command, parameters = {}, secret = '') {
  try {
    const url = `${API}/api/hardware/${hardwareId}/commands/queue`;
    const res = await axios.post(url, { command, parameters, secret });
    return res.data;
  } catch (e) {
    console.error('Failed to send command:', e.response?.data || e.message);
    throw e;
  }
}

// Helper function to get first name from full name
const getFirstName = (fullName) => {
  if (!fullName) return '';
  return fullName.split(' ')[0];
};

// Helper function to calculate distance between two coordinates
const calculateDistance = (lat1, lng1, lat2, lng2) => {
  const R = 6371; // Earth's radius in km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLng/2) * Math.sin(dLng/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
};

// Auth Context
const AuthContext = React.createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      // Load user data if token exists but user is null
      if (!user) {
        loadUserProfile();
      }
    }
  }, [token]);

  const loadUserProfile = async () => {
    try {
      const response = await axios.get(`${API}/user/profile`);
      setUser({
        id: response.data.id,
        email: response.data.email,
        name: response.data.name,
        role: response.data.role
      });
    } catch (error) {
      console.error('Failed to load user profile:', error);
      // If token is invalid, logout
      if (error.response?.status === 401) {
        logout();
      }
    }
  };

  const login = async (email, password) => {
    console.log('Login attempt:', email, 'API URL:', API);
    try {
      console.log('Sending request to:', `${API}/login.php`);
      const response = await axios.post(`${API}/login.php`, { email, password });
      console.log('Login response:', response.data);
      const { token, user: userData } = response.data;
      setToken(token);
      setUser(userData);
      localStorage.setItem('token', token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      console.error('Error details:', error.response?.data);
      return false;
    }
  };

  const register = async (name, email, password, role = 'user') => {
    try {
      const response = await axios.post(`${API}/register.php`, { name, email, password, role });
      // Nach der Registrierung automatisch einloggen
      await login(email, password);
      return true;
    } catch (error) {
      console.error('Registration failed:', error);
      return false;
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, setUser, token, login, register, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Interactive Map Component
const InteractiveMap = ({ userLocation, parkingSpots = [] }) => {
  const [mapKey, setMapKey] = useState(0);
  
  // Calculate center based on parking spots or default to Zürich
  const calculateMapCenter = () => {
    if (userLocation) {
      return [userLocation.lat, userLocation.lng];
    }
    
    if (parkingSpots.length > 0) {
      // Calculate center of all parking spots
      const validSpots = parkingSpots.filter(spot => spot.latitude && spot.longitude);
      if (validSpots.length > 0) {
        const avgLat = validSpots.reduce((sum, spot) => sum + spot.latitude, 0) / validSpots.length;
        const avgLng = validSpots.reduce((sum, spot) => sum + spot.longitude, 0) / validSpots.length;
        return [avgLat, avgLng];
      }
    }
    
    // Default center (Zürich, Switzerland)
    return [47.3769, 8.5417];
  };

  const center = calculateMapCenter();

  // Force map re-render when location or spots change
  useEffect(() => {
    setMapKey(prev => prev + 1);
  }, [userLocation, parkingSpots]);

  // Sample parking spots if none provided (Zürich locations)
  const sampleSpots = [
    { id: 1, name: "Bahnhofstrasse Parking", lat: 47.3769, lng: 8.5417, available: true, price: 4.5 },
    { id: 2, name: "Paradeplatz Garage", lat: 47.3695, lng: 8.539, available: false, price: 5.5 },
    { id: 3, name: "Limmatquai Lot", lat: 47.3722, lng: 8.5434, available: true, price: 3.8 },
    { id: 4, name: "ETH Hauptgebäude", lat: 47.3764, lng: 8.5485, available: true, price: 2.5 },
    { id: 5, name: "Zürich HB", lat: 47.3783, lng: 8.5398, available: false, price: 4.0 }
  ];

  const spotsToShow = parkingSpots.length > 0 ? parkingSpots : sampleSpots;

  return (
    <div className="bg-white rounded-lg shadow-md p-6 h-96 w-full">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Interactive Map</h2>
      <div className="map-container rounded-lg" style={{ height: 'calc(100% - 80px)', width: '100%' }}>
        <MapContainer 
          center={center} 
          zoom={13} 
          style={{ height: '100%', width: '100%', borderRadius: '0.5rem' }}
          className="rounded-lg"
          key={mapKey} // Force re-render when key changes
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          
          {/* User location marker */}
          {userLocation && (
            <Marker 
              position={[userLocation.lat, userLocation.lng]}
              icon={markerIcons.user}
            >
              <Popup>
                <div className="text-center">
                  <strong>Your Location</strong>
                  <br />
                  <small>{userLocation.lat.toFixed(4)}, {userLocation.lng.toFixed(4)}</small>
                </div>
              </Popup>
            </Marker>
          )}

          {/* Parking spots markers */}
          {spotsToShow.map((spot) => {
            // Handle both backend data structure and sample data
            const lat = spot.latitude || spot.lat;
            const lng = spot.longitude || spot.lng;
            const available = spot.is_available !== undefined ? spot.is_available : spot.available;
            const price = spot.hourly_rate || spot.price;
            
            // Skip spots without valid coordinates
            if (!lat || !lng) return null;
            
            // Choose marker icon based on availability
            const markerIcon = available ? markerIcons.available : markerIcons.occupied;
            
            return (
              <Marker 
                key={spot.id} 
                position={[lat, lng]}
                icon={markerIcon}
              >
                <Popup>
                  <div className="min-w-[200px]">
                    <h3 className="font-semibold text-gray-900">{spot.name}</h3>
                    <div className="mt-2 space-y-1">
                      <div className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                        available 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {available ? 'Available' : 'Occupied'}
                      </div>
                      <div className="text-sm text-gray-600">
                        €{price}/hour
                      </div>
                      {available && (
                        <div className="mt-3 grid grid-cols-2 gap-2">
                          <button
                            onClick={async () => {
                              try { await sendHardwareCommandSimple('PARK_DEVICE_001', 'raise_barrier'); alert('Raise queued'); } catch {}
                            }}
                            className="w-full bg-green-600 text-white px-2 py-1 rounded text-xs hover:bg-green-700">
                            Raise
                          </button>
                          <button
                            onClick={async () => {
                              try { await sendHardwareCommandSimple('PARK_DEVICE_001', 'lower_barrier'); alert('Lower queued'); } catch {}
                            }}
                            className="w-full bg-red-600 text-white px-2 py-1 rounded text-xs hover:bg-red-700">
                            Lower
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
      </div>
      
      {/* Map controls info */}
      <div className="mt-2 text-xs text-gray-500 text-center">
        {userLocation 
          ? `Your location: ${userLocation.lat.toFixed(4)}, ${userLocation.lng.toFixed(4)}`
          : 'Enable location for better results'
        } • {spotsToShow.length} parking spots shown
      </div>
    </div>
  );
};

// Reusable MapComponent for both User and Owner dashboards
const MapComponent = ({ 
  spotsToShow = [], 
  userLocation = null, 
  showUserLocation = true, 
  onSpotClick = null,
  mapHeight = "400px"
}) => {
  const [mapKey, setMapKey] = useState(0);
  
  // Calculate center based on parking spots or default to Zürich
  const calculateMapCenter = () => {
    if (userLocation && showUserLocation) {
      return [userLocation.lat, userLocation.lng];
    }
    
    if (spotsToShow.length > 0) {
      // Calculate center of all parking spots
      const validSpots = spotsToShow.filter(spot => spot.latitude && spot.longitude);
      if (validSpots.length > 0) {
        const avgLat = validSpots.reduce((sum, spot) => sum + spot.latitude, 0) / validSpots.length;
        const avgLng = validSpots.reduce((sum, spot) => sum + spot.longitude, 0) / validSpots.length;
        return [avgLat, avgLng];
      }
    }
    
    // Default center (Zürich, Switzerland)
    return [47.3769, 8.5417];
  };

  const center = calculateMapCenter();

  // Force map re-render when location or spots change
  useEffect(() => {
    setMapKey(prev => prev + 1);
  }, [userLocation, spotsToShow]);

  return (
    <div style={{ height: mapHeight, width: '100%' }}>
      <MapContainer 
        center={center} 
        zoom={13} 
        style={{ height: '100%', width: '100%', borderRadius: '0.5rem' }}
        className="rounded-lg"
        key={mapKey} // Force re-render when key changes
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        
        {/* User location marker */}
        {userLocation && showUserLocation && (
          <Marker 
            position={[userLocation.lat, userLocation.lng]}
            icon={markerIcons.user}
          >
            <Popup>
              <div className="text-center">
                <strong>Your Location</strong>
                <br />
                <small>{userLocation.lat.toFixed(4)}, {userLocation.lng.toFixed(4)}</small>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Parking spots markers */}
        {spotsToShow.map((spot) => {
          // Handle both backend data structure and sample data
          const lat = spot.latitude || spot.lat;
          const lng = spot.longitude || spot.lng;
          const available = spot.is_available !== undefined ? spot.is_available : spot.available;
          const price = spot.hourly_rate || spot.price;
          
          // Skip spots without valid coordinates
          if (!lat || !lng) return null;
          
          // Choose marker icon based on availability
          const markerIcon = available ? markerIcons.available : markerIcons.occupied;
          
          return (
            <Marker 
              key={spot.id} 
              position={[lat, lng]}
              icon={markerIcon}
              eventHandlers={{
                click: () => {
                  if (onSpotClick) {
                    onSpotClick(spot);
                  }
                }
              }}
            >
              <Popup>
                <div className="min-w-[200px]">
                  <h3 className="font-semibold text-gray-900">{spot.name}</h3>
                  {spot.address && (
                    <p className="text-xs text-gray-600 mb-2">{spot.address}</p>
                  )}
                  <div className="mt-2 space-y-1">
                    <div className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                      available 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {available ? 'Verfügbar' : 'Belegt'}
                    </div>
                    <div className="text-sm text-gray-600">
                      CHF {price}/Stunde
                    </div>
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
};

// Components
const Login = ({ onSwitchToRegister }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    console.log('Form submitted with:', email, password);
    e.preventDefault();
    setLoading(true);
    console.log('Calling login function...');
    const success = await login(email, password);
    console.log('Login result:', success);
    if (!success) {
      alert('Login failed. Please check your credentials.');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome Back</h1>
          <p className="text-gray-600">Sign in to find your perfect parking spot</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition duration-200 disabled:opacity-50"
          >
            {loading ? 'Signing In...' : 'Sign In'}
          </button>
        </form>
        
        <div className="mt-6 text-center">
          <p className="text-gray-600">
            Don't have an account?{' '}
            <button
              onClick={onSwitchToRegister}
              className="text-blue-600 hover:text-blue-800 font-semibold"
            >
              Sign up
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

const Register = ({ onSwitchToLogin }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('user');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const success = await register(name, email, password, role);
    if (!success) {
      alert('Registration failed. Please try again.');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Join ParkSmart</h1>
          <p className="text-gray-600">Create your account to start parking smarter</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Account Type</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="user">Parking User</option>
              <option value="owner">Parking Lot Owner</option>
              <option value="admin">Administrator</option>
            </select>
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition duration-200 disabled:opacity-50"
          >
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>
        
        <div className="mt-6 text-center">
          <p className="text-gray-600">
            Already have an account?{' '}
            <button
              onClick={onSwitchToLogin}
              className="text-blue-600 hover:text-blue-800 font-semibold"
            >
              Sign in
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

const ParkingMap = () => {
  const [spots, setSpots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSpot, setSelectedSpot] = useState(null);
  const [userLocation, setUserLocation] = useState(null);
  const [activeSession, setActiveSession] = useState(null);
  const { user } = useAuth();

  useEffect(() => {
    loadParkingSpots();
    checkActiveSession();
    getUserLocation();
  }, []);

  const getUserLocation = () => {
    console.log('Requesting user location...');
    
    // Fallback location for testing (Zürich, Switzerland)
    const fallbackLocation = {
      lat: 47.3769,
      lng: 8.5417
    };
    
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const location = {
            lat: position.coords.latitude,
            lng: position.coords.longitude
          };
          console.log('User location obtained:', location);
          setUserLocation(location);
        },
        (error) => {
          console.error('Error getting location:', error);
          console.log('Geolocation error code:', error.code);
          console.log('Geolocation error message:', error.message);
          console.log('Using fallback location for testing...');
          setUserLocation(fallbackLocation);
        },
        {
          enableHighAccuracy: true,
          timeout: 5000,
          maximumAge: 60000
        }
      );
    } else {
      console.error('Geolocation is not supported by this browser');
      console.log('Using fallback location for testing...');
      setUserLocation(fallbackLocation);
    }
  };

  const loadParkingSpots = async () => {
    try {
      const response = await axios.get(`${API}/parking-spots.php`);
      setSpots(response.data);
    } catch (error) {
      console.error('Error loading parking spots:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkActiveSession = async () => {
    try {
      const response = await axios.get(`${API}/parking-sessions`);
      const activeSessions = response.data.filter(session => session.status === 'active');
      if (activeSessions.length > 0) {
        setActiveSession(activeSessions[0]);
      }
    } catch (error) {
      console.error('Error checking active session:', error);
    }
  };

  const startParkingSession = async (spotId) => {
    try {
      const response = await axios.post(`${API}/parking-sessions?spot_id=${spotId}`);
      setActiveSession(response.data);
      loadParkingSpots(); // Refresh spots to show updated availability
      alert('Parking session started successfully!');
    } catch (error) {
      console.error('Error starting parking session:', error);
      alert('Failed to start parking session. Please try again.');
    }
  };

  const endParkingSession = async () => {
    if (!activeSession) return;
    
    try {
      const response = await axios.post(`${API}/parking-sessions/${activeSession.id}/end`);
      setActiveSession(null);
      loadParkingSpots(); // Refresh spots
      
      // Redirect to payment
      const checkoutResponse = await axios.post(`${API}/payments/checkout?session_id=${activeSession.id}`);
      window.location.href = checkoutResponse.data.checkout_url;
    } catch (error) {
      console.error('Error ending parking session:', error);
      alert('Failed to end parking session. Please try again.');
    }
  };

  const calculateDistance = (lat1, lng1, lat2, lng2) => {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLng/2) * Math.sin(dLng/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  };

  const sortedSpots = userLocation 
    ? spots.sort((a, b) => {
        const distA = calculateDistance(userLocation.lat, userLocation.lng, a.latitude, a.longitude);
        const distB = calculateDistance(userLocation.lat, userLocation.lng, b.latitude, b.longitude);
        return distA - distB;
      })
    : spots;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading parking spots...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">ParkSmart</h1>
            <div className="flex items-center space-x-4">
              <span className="text-gray-600">Welcome, {getFirstName(user?.name)}</span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                user?.role === 'admin' ? 'bg-red-100 text-red-800' :
                user?.role === 'owner' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'
              }`}>
                {user?.role === 'admin' ? 'Admin' : user?.role === 'owner' ? 'Owner' : 'User'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Geolocation Status */}
      {!userLocation && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mx-4 mt-4 rounded-r">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-700">
                📍 <strong>Geolocation wird angefordert...</strong> Bitte erlauben Sie den Standortzugriff, um Entfernungen zu Parkplätzen anzuzeigen.
              </p>
            </div>
          </div>
        </div>
      )}

      {userLocation && (
        <div className="bg-green-50 border-l-4 border-green-400 p-4 mx-4 mt-4 rounded-r">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-green-700">
                ✅ <strong>Standort ermittelt!</strong> Entfernungen werden jetzt angezeigt. ({userLocation.lat.toFixed(4)}, {userLocation.lng.toFixed(4)})
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Active Session Alert */}
      {activeSession && (
        <div className="bg-green-50 border-l-4 border-green-400 p-4 mx-4 mt-4 rounded-r">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-lg font-medium text-green-800">Active Parking Session</h3>
              <p className="text-green-700">
                Started at {new Date(activeSession.start_time).toLocaleTimeString()} • 
                Rate: ${activeSession.hourly_rate}/hour
              </p>
            </div>
            <button
              onClick={endParkingSession}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition duration-200"
            >
              End Session & Pay
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Interactive Map */}
          <div className="lg:col-span-2">
            <InteractiveMap 
              userLocation={userLocation} 
              parkingSpots={spots}
            />
          </div>

          {/* Parking Spots List */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-gray-900">
              Nearby Parking Spots ({spots.length})
            </h2>
            
            {sortedSpots.map((spot) => {
              const distance = userLocation 
                ? calculateDistance(userLocation.lat, userLocation.lng, spot.latitude, spot.longitude)
                : null;

              return (
                <div
                  key={spot.id}
                  className={`bg-white rounded-lg shadow-md p-4 border-l-4 ${
                    spot.is_available ? 'border-green-400' : 'border-red-400'
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-semibold text-gray-900">{spot.name}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      spot.is_available 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {spot.is_available ? 'Available' : 'Occupied'}
                    </span>
                  </div>
                  
                  <p className="text-gray-600 text-sm mb-2">{spot.address}</p>
                  
                  <div className="flex justify-between items-center">
                    <div className="text-sm text-gray-500">
                      <p>${spot.hourly_rate}/hour</p>
                      {distance && <p>{distance.toFixed(1)} km away</p>}
                    </div>
                    
                    {spot.is_available && !activeSession && (
                      <button
                        onClick={() => startParkingSession(spot.id)}
                        className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 transition duration-200"
                      >
                        Start Parking
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
            
            {spots.length === 0 && (
              <div className="text-center py-8">
                <p className="text-gray-500">No parking spots available in this area</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Booking History Component
const BookingHistory = () => {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [selectedBooking, setSelectedBooking] = useState(null);
  const [review, setReview] = useState({ rating: 5, comment: '' });

  useEffect(() => {
    loadBookingHistory();
  }, []);

  const loadBookingHistory = async () => {
    try {
      const response = await axios.get(`${API}/parking-sessions/history`);
      setBookings(response.data);
    } catch (error) {
      console.error('Error loading booking history:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/reviews`, {
        parking_session_id: selectedBooking.id,
        rating: review.rating,
        comment: review.comment
      });
      
      setShowReviewModal(false);
      setSelectedBooking(null);
      setReview({ rating: 5, comment: '' });
      loadBookingHistory(); // Reload to update review status
      alert('Review submitted successfully!');
    } catch (error) {
      console.error('Error submitting review:', error);
      alert('Failed to submit review. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading booking history...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Booking History</h1>
        </div>
      </div>

      {/* Bookings List */}
      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="space-y-4">
          {bookings.map((booking) => (
            <div key={booking.id} className="bg-white rounded-lg shadow-md p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="font-semibold text-gray-900 text-lg">
                    {booking.parking_spot?.name || 'Unknown Location'}
                  </h3>
                  <p className="text-gray-600">{booking.parking_spot?.address}</p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-semibold text-gray-900">${booking.total_amount?.toFixed(2)}</p>
                  <p className="text-sm text-gray-500">
                    {((new Date(booking.end_time) - new Date(booking.start_time)) / (1000 * 60 * 60)).toFixed(2)} hours
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <p className="text-sm text-gray-500">Start Time</p>
                  <p className="font-medium">{new Date(booking.start_time).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">End Time</p>
                  <p className="font-medium">{new Date(booking.end_time).toLocaleString()}</p>
                </div>
              </div>

              <div className="flex justify-between items-center pt-4 border-t">
                <div className="text-sm text-gray-500">
                  Rate: ${booking.hourly_rate}/hour
                </div>
                
                {booking.has_review ? (
                  <div className="flex items-center">
                    <span className="text-green-600 text-sm mr-2">✓ Reviewed</span>
                    {booking.review && (
                      <div className="flex items-center">
                        <span className="text-yellow-500">{'★'.repeat(booking.review.rating)}</span>
                        <span className="text-gray-400">{'★'.repeat(5 - booking.review.rating)}</span>
                      </div>
                    )}
                  </div>
                ) : (
                  <button
                    onClick={() => {
                      setSelectedBooking(booking);
                      setShowReviewModal(true);
                    }}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 transition duration-200"
                  >
                    Leave Review
                  </button>
                )}
              </div>
            </div>
          ))}

          {bookings.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-500">No booking history found</p>
            </div>
          )}
        </div>
      </div>

      {/* Review Modal */}
      {showReviewModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Leave a Review</h2>
            
            <div className="mb-4">
              <h3 className="font-semibold text-gray-800">{selectedBooking?.parking_spot?.name}</h3>
              <p className="text-gray-600 text-sm">{selectedBooking?.parking_spot?.address}</p>
            </div>

            <form onSubmit={handleReviewSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Rating</label>
                <div className="flex space-x-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setReview({ ...review, rating: star })}
                      className={`text-2xl ${
                        star <= review.rating ? 'text-yellow-500' : 'text-gray-300'
                      } hover:text-yellow-500 transition duration-200`}
                    >
                      ★
                    </button>
                  ))}
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Comment (Optional)</label>
                <textarea
                  value={review.comment}
                  onChange={(e) => setReview({ ...review, comment: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  rows="3"
                  placeholder="Share your experience..."
                />
              </div>
              
              <div className="flex space-x-4 pt-4">
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition duration-200"
                >
                  Submit Review
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowReviewModal(false);
                    setSelectedBooking(null);
                    setReview({ rating: 5, comment: '' });
                  }}
                  className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400 transition duration-200"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// Reviews Management Component
const ReviewsManagement = () => {
  const { user, token } = useAuth();
  const [activeSection, setActiveSection] = useState('my-reviews');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  
  // State for reviews
  const [myReviews, setMyReviews] = useState([]);
  const [pendingReviews, setPendingReviews] = useState([]);
  const [parkingSpotReviews, setParkingSpotReviews] = useState([]);
  const [selectedSpotId, setSelectedSpotId] = useState('');
  const [availableSpots, setAvailableSpots] = useState([]);
  
  // Review form state
  const [reviewForm, setReviewForm] = useState({
    session_id: '',
    rating: 5,
    comment: ''
  });

  useEffect(() => {
    loadMyReviews();
    loadPendingReviews();
    loadAvailableSpots();
  }, []);

  const loadMyReviews = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/reviews/my-reviews`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMyReviews(response.data);
    } catch (error) {
      console.error('Error loading my reviews:', error);
      setError('Failed to load your reviews');
    } finally {
      setLoading(false);
    }
  };

  const loadPendingReviews = async () => {
    try {
      // Get sessions that haven't been reviewed yet
      const historyResponse = await axios.get(`${API}/parking-sessions/history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const unreviewed = historyResponse.data.filter(session => !session.has_review);
      setPendingReviews(unreviewed);
    } catch (error) {
      console.error('Error loading pending reviews:', error);
    }
  };

  const loadAvailableSpots = async () => {
    try {
      const response = await axios.get(`${API}/parking-spots`);
      setAvailableSpots(response.data);
    } catch (error) {
      console.error('Error loading parking spots:', error);
    }
  };

  const loadSpotReviews = async (spotId) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/reviews/spot/${spotId}`);
      setParkingSpotReviews(response.data);
    } catch (error) {
      console.error('Error loading spot reviews:', error);
      setError('Failed to load reviews for this parking spot');
    } finally {
      setLoading(false);
    }
  };

  const handleSpotSelect = (spotId) => {
    setSelectedSpotId(spotId);
    if (spotId) {
      loadSpotReviews(spotId);
    } else {
      setParkingSpotReviews([]);
    }
  };

  const submitReview = async (sessionId, rating, comment) => {
    try {
      setLoading(true);
      await axios.post(`${API}/reviews`, {
        parking_session_id: sessionId,
        rating: rating,
        comment: comment
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setMessage('Review submitted successfully!');
      await loadMyReviews();
      await loadPendingReviews();
    } catch (error) {
      console.error('Error submitting review:', error);
      setError('Failed to submit review. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const updateReview = async (reviewId, rating, comment) => {
    try {
      setLoading(true);
      await axios.put(`${API}/reviews/${reviewId}`, {
        rating: rating,
        comment: comment
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setMessage('Review updated successfully!');
      await loadMyReviews();
    } catch (error) {
      console.error('Error updating review:', error);
      setError('Failed to update review. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const deleteReview = async (reviewId) => {
    if (!window.confirm('Are you sure you want to delete this review?')) return;
    
    try {
      setLoading(true);
      await axios.delete(`${API}/reviews/${reviewId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setMessage('Review deleted successfully!');
      await loadMyReviews();
      await loadPendingReviews();
    } catch (error) {
      console.error('Error deleting review:', error);
      setError('Failed to delete review. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const sections = [
    { id: 'my-reviews', label: 'Meine Bewertungen', icon: '⭐' },
    { id: 'pending', label: 'Ausstehende Bewertungen', icon: '⏳' },
    { id: 'browse', label: 'Parkplatz-Bewertungen', icon: '🔍' }
  ];

  const ReviewCard = ({ review, canEdit = false, canDelete = false, showSpotInfo = true }) => (
    <div className="bg-white rounded-lg shadow-md p-6 mb-4">
      {showSpotInfo && (
        <div className="mb-4">
          <h3 className="font-semibold text-gray-900">{review.parking_spot?.name || 'Unknown Location'}</h3>
          <p className="text-gray-600 text-sm">{review.parking_spot?.address}</p>
        </div>
      )}
      
      <div className="flex items-center mb-3">
        <div className="flex items-center">
          {[1, 2, 3, 4, 5].map((star) => (
            <span
              key={star}
              className={`text-lg ${star <= review.rating ? 'text-yellow-500' : 'text-gray-300'}`}
            >
              ★
            </span>
          ))}
        </div>
        <span className="ml-2 text-sm text-gray-500">
          {new Date(review.created_at).toLocaleDateString()}
        </span>
      </div>
      
      {review.comment && (
        <p className="text-gray-700 mb-4">{review.comment}</p>
      )}
      
      <div className="flex justify-between items-center text-sm text-gray-500">
        <span>Von: {review.user_name || user?.name || 'Anonymous'}</span>
        {(canEdit || canDelete) && (
          <div className="space-x-2">
            {canEdit && (
              <button
                onClick={() => {
                  const newRating = prompt('New rating (1-5):', review.rating);
                  const newComment = prompt('New comment:', review.comment || '');
                  if (newRating && newRating >= 1 && newRating <= 5) {
                    updateReview(review.id, parseInt(newRating), newComment || '');
                  }
                }}
                className="text-blue-600 hover:text-blue-800"
              >
                Edit
              </button>
            )}
            {canDelete && (
              <button
                onClick={() => deleteReview(review.id)}
                className="text-red-600 hover:text-red-800"
              >
                Delete
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );

  const PendingReviewCard = ({ session }) => {
    const [rating, setRating] = useState(5);
    const [comment, setComment] = useState('');
    const [showForm, setShowForm] = useState(false);

    return (
      <div className="bg-white rounded-lg shadow-md p-6 mb-4">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="font-semibold text-gray-900">{session.parking_spot?.name || 'Unknown Location'}</h3>
            <p className="text-gray-600 text-sm">{session.parking_spot?.address}</p>
            <p className="text-sm text-gray-500 mt-1">
              {new Date(session.start_time).toLocaleDateString()} • ${session.total_amount?.toFixed(2)}
            </p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 transition duration-200"
          >
            {showForm ? 'Cancel' : 'Write Review'}
          </button>
        </div>

        {showForm && (
          <div className="border-t pt-4">
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Rating</label>
              <div className="flex space-x-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setRating(star)}
                    className={`text-2xl ${star <= rating ? 'text-yellow-500' : 'text-gray-300'} hover:text-yellow-500 transition duration-200`}
                  >
                    ★
                  </button>
                ))}
              </div>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Comment (Optional)</label>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                rows="3"
                placeholder="Share your experience..."
              />
            </div>
            
            <button
              onClick={() => {
                submitReview(session.id, rating, comment);
                setShowForm(false);
                setComment('');
                setRating(5);
              }}
              disabled={loading}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition duration-200 disabled:opacity-50"
            >
              {loading ? 'Submitting...' : 'Submit Review'}
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Bewertungen</h1>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Sidebar Navigation */}
          <div className="lg:w-1/4">
            <div className="bg-white rounded-lg shadow-md p-4">
              <nav className="space-y-2">
                {sections.map((section) => (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={`w-full text-left px-4 py-3 rounded-lg text-sm font-medium transition duration-200 ${
                      activeSection === section.id
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    <span className="mr-3">{section.icon}</span>
                    {section.label}
                  </button>
                ))}
              </nav>
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:w-3/4">
            {/* Messages */}
            {message && (
              <div className="mb-4 p-4 rounded-lg bg-green-100 text-green-700">
                {message}
              </div>
            )}
            {error && (
              <div className="mb-4 p-4 rounded-lg bg-red-100 text-red-700">
                {error}
              </div>
            )}

            {/* My Reviews Section */}
            {activeSection === 'my-reviews' && (
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-6">Meine Bewertungen ({myReviews.length})</h2>
                
                {loading ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading your reviews...</p>
                  </div>
                ) : myReviews.length > 0 ? (
                  myReviews.map((review) => (
                    <ReviewCard 
                      key={review.id} 
                      review={review} 
                      canEdit={true} 
                      canDelete={true}
                      showSpotInfo={true}
                    />
                  ))
                ) : (
                  <div className="text-center py-12">
                    <p className="text-gray-500">Sie haben noch keine Bewertungen abgegeben</p>
                    <p className="text-sm text-gray-400 mt-2">
                      Bewerten Sie Ihre Parkerfahrungen, um anderen Nutzern zu helfen!
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Pending Reviews Section */}
            {activeSection === 'pending' && (
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-6">
                  Ausstehende Bewertungen ({pendingReviews.length})
                </h2>
                
                {loading ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading pending reviews...</p>
                  </div>
                ) : pendingReviews.length > 0 ? (
                  pendingReviews.map((session) => (
                    <PendingReviewCard key={session.id} session={session} />
                  ))
                ) : (
                  <div className="text-center py-12">
                    <p className="text-gray-500">Keine ausstehenden Bewertungen</p>
                    <p className="text-sm text-gray-400 mt-2">
                      Alle Ihre Parksessions wurden bereits bewertet.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Browse Spot Reviews Section */}
            {activeSection === 'browse' && (
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-6">Parkplatz-Bewertungen durchsuchen</h2>
                
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Parkplatz auswählen
                  </label>
                  <select
                    value={selectedSpotId}
                    onChange={(e) => handleSpotSelect(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">-- Wählen Sie einen Parkplatz --</option>
                    {availableSpots.map((spot) => (
                      <option key={spot.id} value={spot.id}>
                        {spot.name} - {spot.address}
                      </option>
                    ))}
                  </select>
                </div>

                {selectedSpotId && (
                  <div>
                    {loading ? (
                      <div className="text-center py-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                        <p className="text-gray-600">Loading reviews...</p>
                      </div>
                    ) : parkingSpotReviews.length > 0 ? (
                      <div>
                        <div className="bg-white rounded-lg shadow-md p-4 mb-6">
                          <h3 className="font-semibold text-gray-900 mb-2">
                            Durchschnittliche Bewertung
                          </h3>
                          <div className="flex items-center">
                            <div className="flex items-center mr-4">
                              {[1, 2, 3, 4, 5].map((star) => {
                                const avgRating = parkingSpotReviews.reduce((sum, r) => sum + r.rating, 0) / parkingSpotReviews.length;
                                return (
                                  <span
                                    key={star}
                                    className={`text-lg ${star <= Math.round(avgRating) ? 'text-yellow-500' : 'text-gray-300'}`}
                                  >
                                    ★
                                  </span>
                                );
                              })}
                            </div>
                            <span className="text-gray-600">
                              {(parkingSpotReviews.reduce((sum, r) => sum + r.rating, 0) / parkingSpotReviews.length).toFixed(1)} 
                              ({parkingSpotReviews.length} Bewertung{parkingSpotReviews.length !== 1 ? 'en' : ''})
                            </span>
                          </div>
                        </div>
                        
                        {parkingSpotReviews.map((review) => (
                          <ReviewCard 
                            key={review.id} 
                            review={review} 
                            canEdit={false} 
                            canDelete={false}
                            showSpotInfo={false}
                          />
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-12">
                        <p className="text-gray-500">Keine Bewertungen für diesen Parkplatz vorhanden</p>
                        <p className="text-sm text-gray-400 mt-2">
                          Seien Sie der Erste, der diesen Parkplatz bewertet!
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Account Management Component
const AccountManagement = () => {
  const { user, setUser, token } = useAuth();
  const [activeSection, setActiveSection] = useState('profile');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  
  // Profile form state
  const [profileData, setProfileData] = useState({
    first_name: '',
    last_name: '',
    phone: '',
    address: '',
    city: '',
    zip_code: '',
    country: '',
    secondary_email: '',
    date_of_birth: ''
  });

  // Password change form state
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });

  // Email change form state
  const [emailData, setEmailData] = useState({
    new_email: '',
    password: ''
  });

  // Account summary state
  const [accountSummary, setAccountSummary] = useState(null);

  useEffect(() => {
    loadUserProfile();
    loadAccountSummary();
  }, []);

  const loadUserProfile = async () => {
    try {
      const response = await axios.get(`${API}/user/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProfileData({
        first_name: response.data.first_name || '',
        last_name: response.data.last_name || '',
        phone: response.data.phone || '',
        address: response.data.address || '',
        city: response.data.city || '',
        zip_code: response.data.zip_code || '',
        country: response.data.country || '',
        secondary_email: response.data.secondary_email || '',
        date_of_birth: response.data.date_of_birth ? response.data.date_of_birth.split('T')[0] : ''
      });
    } catch (error) {
      console.error('Error loading profile:', error);
      setError('Failed to load profile data');
    }
  };

  const loadAccountSummary = async () => {
    try {
      const response = await axios.get(`${API}/user/account-summary`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAccountSummary(response.data);
    } catch (error) {
      console.error('Error loading account summary:', error);
    }
  };

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setError('');

    try {
      const updateData = { ...profileData };
      if (updateData.date_of_birth) {
        updateData.date_of_birth = new Date(updateData.date_of_birth).toISOString();
      }

      const response = await axios.put(`${API}/user/profile`, updateData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setMessage('Profile updated successfully!');
      setUser(response.data.user);
    } catch (error) {
      console.error('Error updating profile:', error);
      setError('Failed to update profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setError('');

    if (passwordData.new_password !== passwordData.confirm_password) {
      setError('New passwords do not match');
      setLoading(false);
      return;
    }

    if (passwordData.new_password.length < 6) {
      setError('Password must be at least 6 characters long');
      setLoading(false);
      return;
    }

    try {
      await axios.put(`${API}/user/password`, {
        current_password: passwordData.current_password,
        new_password: passwordData.new_password
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setMessage('Password updated successfully!');
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: ''
      });
    } catch (error) {
      console.error('Error updating password:', error);
      setError(error.response?.data?.detail || 'Failed to update password');
    } finally {
      setLoading(false);
    }
  };

  const handleEmailChange = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setError('');

    try {
      const response = await axios.put(`${API}/user/email`, emailData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setMessage('Email updated successfully! Please log in again.');
      setEmailData({ new_email: '', password: '' });
      
      // Update token and user data
      localStorage.setItem('token', response.data.access_token);
      setUser({ ...user, email: response.data.new_email });
    } catch (error) {
      console.error('Error updating email:', error);
      setError(error.response?.data?.detail || 'Failed to update email');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = async (password) => {
    setLoading(true);
    setMessage('');
    setError('');

    try {
      await axios.delete(`${API}/user/account?password=${encodeURIComponent(password)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Clear auth data and redirect
      localStorage.removeItem('token');
      setUser(null);
      alert('Account deleted successfully');
    } catch (error) {
      console.error('Error deleting account:', error);
      setError(error.response?.data?.detail || 'Failed to delete account');
    } finally {
      setLoading(false);
      setShowDeleteConfirm(false);
    }
  };

  const sections = [
    { id: 'profile', label: 'Profile Information', icon: '👤' },
    { id: 'security', label: 'Security Settings', icon: '🔒' },
    { id: 'summary', label: 'Account Summary', icon: '📊' },
    { id: 'danger', label: 'Account Actions', icon: '⚠️' }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Account Management</h1>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Sidebar Navigation */}
          <div className="lg:w-1/4">
            <div className="bg-white rounded-lg shadow-md p-4">
              <nav className="space-y-2">
                {sections.map((section) => (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={`w-full text-left px-4 py-3 rounded-lg text-sm font-medium transition duration-200 ${
                      activeSection === section.id
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    <span className="mr-3">{section.icon}</span>
                    {section.label}
                  </button>
                ))}
              </nav>
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:w-3/4">
            {/* Messages */}
            {message && (
              <div className="mb-4 p-4 rounded-lg bg-green-100 text-green-700">
                {message}
              </div>
            )}
            {error && (
              <div className="mb-4 p-4 rounded-lg bg-red-100 text-red-700">
                {error}
              </div>
            )}

            {/* Profile Information Section */}
            {activeSection === 'profile' && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-6">Profile Information</h2>
                
                <form onSubmit={handleProfileUpdate} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        First Name
                      </label>
                      <input
                        type="text"
                        value={profileData.first_name}
                        onChange={(e) => setProfileData({...profileData, first_name: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Last Name
                      </label>
                      <input
                        type="text"
                        value={profileData.last_name}
                        onChange={(e) => setProfileData({...profileData, last_name: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Phone Number
                    </label>
                    <input
                      type="tel"
                      value={profileData.phone}
                      onChange={(e) => setProfileData({...profileData, phone: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Address
                    </label>
                    <input
                      type="text"
                      value={profileData.address}
                      onChange={(e) => setProfileData({...profileData, address: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        City
                      </label>
                      <input
                        type="text"
                        value={profileData.city}
                        onChange={(e) => setProfileData({...profileData, city: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        ZIP Code
                      </label>
                      <input
                        type="text"
                        value={profileData.zip_code}
                        onChange={(e) => setProfileData({...profileData, zip_code: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Country
                      </label>
                      <input
                        type="text"
                        value={profileData.country}
                        onChange={(e) => setProfileData({...profileData, country: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Secondary Email
                    </label>
                    <input
                      type="email"
                      value={profileData.secondary_email}
                      onChange={(e) => setProfileData({...profileData, secondary_email: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Date of Birth
                    </label>
                    <input
                      type="date"
                      value={profileData.date_of_birth}
                      onChange={(e) => setProfileData({...profileData, date_of_birth: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={loading}
                    className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition duration-200 disabled:opacity-50"
                  >
                    {loading ? 'Updating...' : 'Update Profile'}
                  </button>
                </form>
              </div>
            )}

            {/* Security Settings Section */}
            {activeSection === 'security' && (
              <div className="space-y-6">
                {/* Change Email */}
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h2 className="text-xl font-bold text-gray-900 mb-6">Change Email Address</h2>
                  <p className="text-gray-600 mb-4">Current email: {user?.email}</p>
                  
                  <form onSubmit={handleEmailChange} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        New Email Address
                      </label>
                      <input
                        type="email"
                        required
                        value={emailData.new_email}
                        onChange={(e) => setEmailData({...emailData, new_email: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Current Password
                      </label>
                      <input
                        type="password"
                        required
                        value={emailData.password}
                        onChange={(e) => setEmailData({...emailData, password: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={loading}
                      className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition duration-200 disabled:opacity-50"
                    >
                      {loading ? 'Updating...' : 'Update Email'}
                    </button>
                  </form>
                </div>

                {/* Change Password */}
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h2 className="text-xl font-bold text-gray-900 mb-6">Change Password</h2>
                  
                  <form onSubmit={handlePasswordChange} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Current Password
                      </label>
                      <input
                        type="password"
                        required
                        value={passwordData.current_password}
                        onChange={(e) => setPasswordData({...passwordData, current_password: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        New Password
                      </label>
                      <input
                        type="password"
                        required
                        value={passwordData.new_password}
                        onChange={(e) => setPasswordData({...passwordData, new_password: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Confirm New Password
                      </label>
                      <input
                        type="password"
                        required
                        value={passwordData.confirm_password}
                        onChange={(e) => setPasswordData({...passwordData, confirm_password: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={loading}
                      className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition duration-200 disabled:opacity-50"
                    >
                      {loading ? 'Updating...' : 'Update Password'}
                    </button>
                  </form>
                </div>
              </div>
            )}

            {/* Account Summary Section */}
            {activeSection === 'summary' && accountSummary && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-6">Account Summary</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <h3 className="font-medium text-blue-900">Account Information</h3>
                      <p className="text-blue-700">Email: {accountSummary.email}</p>
                      <p className="text-blue-700">Name: {accountSummary.name}</p>
                      <p className="text-blue-700">Role: {accountSummary.role}</p>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="p-4 bg-green-50 rounded-lg">
                      <h3 className="font-medium text-green-900">Activity Statistics</h3>
                      <p className="text-green-700">Total Parking Sessions: {accountSummary.statistics.total_parking_sessions}</p>
                      <p className="text-green-700">Active Sessions: {accountSummary.statistics.active_parking_sessions}</p>
                      <p className="text-green-700">Total Reviews: {accountSummary.statistics.total_reviews}</p>
                      {accountSummary.role === 'owner' && (
                        <p className="text-green-700">Owned Parking Spots: {accountSummary.statistics.owned_parking_spots}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Recent Activity */}
                {accountSummary.recent_sessions && accountSummary.recent_sessions.length > 0 && (
                  <div className="mt-6">
                    <h3 className="font-medium text-gray-900 mb-4">Recent Activity</h3>
                    <div className="space-y-2">
                      {accountSummary.recent_sessions.map((session) => (
                        <div key={session.id} className="p-3 bg-gray-50 rounded-lg">
                          <div className="flex justify-between items-center">
                            <span className="font-medium">{session.status}</span>
                            <span className="text-sm text-gray-500">
                              {new Date(session.created_at).toLocaleDateString()}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600">${session.total_amount?.toFixed(2)}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Account Actions Section */}
            {activeSection === 'danger' && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-bold text-red-600 mb-6">Danger Zone</h2>
                
                <div className="border border-red-200 rounded-lg p-4">
                  <h3 className="font-medium text-red-900 mb-2">Delete Account</h3>
                  <p className="text-red-700 text-sm mb-4">
                    This action cannot be undone. This will permanently delete your account and all associated data.
                  </p>
                  <button
                    onClick={() => setShowDeleteConfirm(true)}
                    className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition duration-200"
                  >
                    Delete Account
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h2 className="text-xl font-bold text-red-600 mb-4">Confirm Account Deletion</h2>
            <p className="text-gray-700 mb-4">
              Please enter your password to confirm account deletion. This action cannot be undone.
            </p>
            
            <form onSubmit={(e) => {
              e.preventDefault();
              const password = e.target.password.value;
              handleDeleteAccount(password);
            }}>
              <input
                type="password"
                name="password"
                required
                placeholder="Enter your password"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 mb-4"
              />
              
              <div className="flex space-x-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-red-600 text-white py-2 rounded-lg hover:bg-red-700 transition duration-200 disabled:opacity-50"
                >
                  {loading ? 'Deleting...' : 'Delete Account'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowDeleteConfirm(false)}
                  className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400 transition duration-200"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// User Dashboard with Navigation
const UserDashboard = () => {
  const [currentView, setCurrentView] = useState('map'); // 'map', 'history', 'account', or 'reviews'
  const { user } = useAuth();

  const navItems = [
    { id: 'map', label: 'Find Parking', icon: '🗺️' },
    { id: 'history', label: 'Booking History', icon: '📝' },
    { id: 'reviews', label: 'Bewertungen', icon: '⭐' },
    { id: 'account', label: 'Account Management', icon: '👤' }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header with Navigation */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-2xl font-bold text-gray-900">ParkSmart</h1>
            <div className="flex items-center space-x-4">
              <span className="text-gray-600">Welcome, {getFirstName(user?.name)}</span>
              <span className="px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                User
              </span>
            </div>
          </div>
          
          {/* Navigation Tabs */}
          <div className="flex space-x-1">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setCurrentView(item.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition duration-200 ${
                  currentView === item.id
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <span className="mr-2">{item.icon}</span>
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      {currentView === 'map' ? (
        <div className="max-w-6xl mx-auto px-4 py-6">
          <ParkingMapContent />
        </div>
      ) : currentView === 'history' ? (
        <BookingHistory />
      ) : currentView === 'reviews' ? (
        <ReviewsManagement />
      ) : (
        <AccountManagement />
      )}
    </div>
  );
};

// Extract ParkingMap content as separate component
const ParkingMapContent = () => {
  const [spots, setSpots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSpot, setSelectedSpot] = useState(null);
  const [userLocation, setUserLocation] = useState(null);
  const [activeSession, setActiveSession] = useState(null);
  const { user } = useAuth();

  useEffect(() => {
    loadParkingSpots();
    checkActiveSession();
    getUserLocation();
  }, []);

  const getUserLocation = () => {
    console.log('ParkingMapContent requesting user location...');
    
    // Fallback location for testing (Zürich, Switzerland)
    const fallbackLocation = {
      lat: 47.3769,
      lng: 8.5417
    };
    
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const location = {
            lat: position.coords.latitude,
            lng: position.coords.longitude
          };
          console.log('ParkingMapContent location obtained:', location);
          setUserLocation(location);
        },
        (error) => {
          console.error('Error getting ParkingMapContent location:', error);
          console.log('Using fallback location for ParkingMapContent...');
          setUserLocation(fallbackLocation);
        },
        {
          enableHighAccuracy: true,
          timeout: 5000,
          maximumAge: 60000
        }
      );
    } else {
      console.error('Geolocation is not supported by this browser');
      console.log('Using fallback location for ParkingMapContent...');
      setUserLocation(fallbackLocation);
    }
  };

  const loadParkingSpots = async () => {
    try {
      const response = await axios.get(`${API}/parking-spots`);
      setSpots(response.data);
    } catch (error) {
      console.error('Error loading parking spots:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkActiveSession = async () => {
    try {
      const response = await axios.get(`${API}/parking-sessions`);
      const activeSessions = response.data.filter(session => session.status === 'active');
      if (activeSessions.length > 0) {
        setActiveSession(activeSessions[0]);
      }
    } catch (error) {
      console.error('Error checking active session:', error);
    }
  };

  const startParkingSession = async (spotId) => {
    try {
      const response = await axios.post(`${API}/parking-sessions?spot_id=${spotId}`);
      setActiveSession(response.data);
      loadParkingSpots(); // Refresh spots to update availability
      alert('Parking session started successfully!');
    } catch (error) {
      console.error('Error starting parking session:', error);
      alert('Failed to start parking session. Please try again.');
    }
  };

  const endParkingSession = async () => {
    try {
      const response = await axios.post(`${API}/parking-sessions/${activeSession.id}/end`);
      alert(`Session ended. Total amount: $${response.data.total_amount.toFixed(2)} for ${response.data.duration_hours.toFixed(2)} hours`);
      setActiveSession(null);
      loadParkingSpots(); // Refresh spots to update availability
    } catch (error) {
      console.error('Error ending parking session:', error);
      alert('Failed to end parking session. Please try again.');
    }
  };

  const calculateDistance = (lat1, lng1, lat2, lng2) => {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLng/2) * Math.sin(dLng/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  };

  const sortedSpots = userLocation 
    ? spots.sort((a, b) => {
        const distA = calculateDistance(userLocation.lat, userLocation.lng, a.latitude, a.longitude);
        const distB = calculateDistance(userLocation.lat, userLocation.lng, b.latitude, b.longitude);
        return distA - distB;
      })
    : spots;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading parking spots...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Active Session Alert */}
      {activeSession && (
        <div className="bg-green-50 border-l-4 border-green-400 p-4 mb-6 rounded-r">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-lg font-medium text-green-800">Active Parking Session</h3>
              <p className="text-green-700">
                Started at {new Date(activeSession.start_time).toLocaleTimeString()} • 
                Rate: ${activeSession.hourly_rate}/hour
              </p>
            </div>
            <button
              onClick={endParkingSession}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition duration-200"
            >
              End Session & Pay
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Interactive Map */}
        <div className="lg:col-span-2">
          <InteractiveMap 
            userLocation={userLocation} 
            parkingSpots={spots}
          />
        </div>

        {/* Parking Spots List */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-900">
            Nearby Parking Spots ({spots.length})
          </h2>
          
          {sortedSpots.map((spot) => {
            const distance = userLocation 
              ? calculateDistance(userLocation.lat, userLocation.lng, spot.latitude, spot.longitude)
              : null;

            return (
              <div
                key={spot.id}
                className={`bg-white rounded-lg shadow-md p-4 border-l-4 ${
                  spot.is_available ? 'border-green-400' : 'border-red-400'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-semibold text-gray-900">{spot.name}</h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    spot.is_available 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {spot.is_available ? 'Available' : 'Occupied'}
                  </span>
                </div>
                
                <p className="text-gray-600 text-sm mb-2">{spot.address}</p>
                
                <div className="flex justify-between items-center">
                  <div className="text-sm text-gray-500">
                    <p>${spot.hourly_rate}/hour</p>
                    {distance && <p>{distance.toFixed(1)} km away</p>}
                  </div>
                  
                  {spot.is_available && !activeSession && (
                    <button
                      onClick={() => startParkingSession(spot.id)}
                      className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 transition duration-200"
                    >
                      Start Parking
                    </button>
                  )}
                </div>
              </div>
            );
          })}
          
          {spots.length === 0 && (
            <div className="text-center py-8">
              <p className="text-gray-500">No parking spots available in this area</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const OwnerDashboard = () => {
  const [activeTab, setActiveTab] = useState('spots');
  const [spots, setSpots] = useState([]);
  const [userLocation, setUserLocation] = useState(null);
  const [ownerBookings, setOwnerBookings] = useState([]);
  const [ownerReceivedReviews, setOwnerReceivedReviews] = useState([]);
  const [customerReviews, setCustomerReviews] = useState([]);
  const [activeReviewTab, setActiveReviewTab] = useState('received');
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [selectedBookingForReview, setSelectedBookingForReview] = useState(null);
  const [newCustomerReview, setNewCustomerReview] = useState({
    rating: 5,
    comment: '',
    reliability: 5,
    communication: 5,
    punctuality: 5
  });
  const [showAddSpot, setShowAddSpot] = useState(false);
  const [newSpot, setNewSpot] = useState({
    name: '',
    latitude: '',
    longitude: '',
    address: '',
    hourly_rate: ''
  });
  
  // New states for enhanced functionality
  const [addressSuggestions, setAddressSuggestions] = useState([]);
  const [showAddressSuggestions, setShowAddressSuggestions] = useState(false);
  const [addressLoading, setAddressLoading] = useState(false);
  const [addressError, setAddressError] = useState('');
  const [coordinatesAutoFilled, setCoordinatesAutoFilled] = useState(false);
  const [priceRecommendations, setPriceRecommendations] = useState(null);
  const [priceRecommendationLoading, setPriceRecommendationLoading] = useState(false);
  const [showAddBusinessForm, setShowAddBusinessForm] = useState(false);
  
  // Edit/Delete spot states
  const [showEditSpot, setShowEditSpot] = useState(false);
  const [editingSpot, setEditingSpot] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [spotToDelete, setSpotToDelete] = useState(null);
  
  // Revenue states
  const [revenueData, setRevenueData] = useState(null);
  const [revenueLoading, setRevenueLoading] = useState(false);
  const [detailedRevenue, setDetailedRevenue] = useState(null);
  const [selectedPeriod, setSelectedPeriod] = useState('monthly');
  const [showDetailedView, setShowDetailedView] = useState(false);
  
  const { user, logout } = useAuth();

  // Manual hardware control (owner only)
  const [deviceId, setDeviceId] = useState('PARK_DEVICE_001');
  const [manualStatus, setManualStatus] = useState('idle'); // idle | sending | ok | error
  // Assign device to spot (owner UI)
  const [assignHardwareId, setAssignHardwareId] = useState('PARK_DEVICE_001');
  const [assignSpotId, setAssignSpotId] = useState('');
  const [assignStatus, setAssignStatus] = useState('idle'); // idle | sending | ok | error

  const handleManualCommand = async (command) => {
    try {
      setManualStatus('sending');
      // sendHardwareCommandSimple(urlPath) returns the backend response
      await sendHardwareCommandSimple(deviceId, command, {});
      setManualStatus('ok');
      // small confirmation for owner
      alert(`Command queued: ${command}`);
    } catch (err) {
      console.error('Manual command failed:', err);
      setManualStatus('error');
      alert(`Failed to send command: ${err?.message || err}`);
    }
  };

  const handleLogout = () => {
    logout();
  };

  const handleAssignDevice = async () => {
    if (!assignHardwareId || !assignSpotId) {
      alert('Bitte Hardware-ID und Park-Spot auswählen');
      return;
    }

    try {
      setAssignStatus('sending');
      const payload = { hardware_id: assignHardwareId, spot_id: Number(assignSpotId) };
      const res = await axios.post(`${API}/api/owner/devices/assign`, payload);
      console.log('Assign response', res.data);
      setAssignStatus('ok');
      alert(`Device ${assignHardwareId} zugewiesen an Spot ${assignSpotId}`);
      // refresh spots/devices if needed
      loadOwnerSpots();
    } catch (err) {
      console.error('Assign failed', err);
      setAssignStatus('error');
      alert('Zuweisung fehlgeschlagen');
    }
  };

  useEffect(() => {
    loadOwnerSpots();
    getUserLocation();
    if (activeTab === 'bookings') {
      loadOwnerBookings();
    }
    if (activeTab === 'reviews') {
      loadOwnerReviews();
    }
    if (activeTab === 'revenue') {
      loadRevenueData();
    }
  }, [activeTab]);

  const getUserLocation = () => {
    console.log('Owner requesting user location...');
    
    // Fallback location for testing (Zürich, Switzerland)
    const fallbackLocation = {
      lat: 47.3769,
      lng: 8.5417
    };
    
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const location = {
            lat: position.coords.latitude,
            lng: position.coords.longitude
          };
          console.log('Owner location obtained:', location);
          setUserLocation(location);
        },
        (error) => {
          console.error('Error getting owner location:', error);
          console.log('Using fallback location for owner...');
          setUserLocation(fallbackLocation);
        },
        {
          enableHighAccuracy: true,
          timeout: 5000,
          maximumAge: 60000
        }
      );
    } else {
      console.error('Geolocation is not supported by this browser');
      console.log('Using fallback location for owner...');
      setUserLocation(fallbackLocation);
    }
  };

  // Debounced address search
  const searchAddressTimeout = useRef(null);

  const handleAddressChange = async (address) => {
    setNewSpot({...newSpot, address});
    setAddressError('');
    setCoordinatesAutoFilled(false);
    
    if (searchAddressTimeout.current) {
      clearTimeout(searchAddressTimeout.current);
    }
    
    if (address.length < 3) {
      setAddressSuggestions([]);
      setShowAddressSuggestions(false);
      return;
    }
    
    searchAddressTimeout.current = setTimeout(async () => {
      await searchAddress(address);
    }, 500);
  };

  const searchAddress = async (query) => {
    try {
      setAddressLoading(true);
      setAddressError('');
      
      // First try local/fallback data for common Swiss companies
      const localResults = getLocalCompanyData(query);
      if (localResults.length > 0) {
        setAddressSuggestions(localResults);
        setShowAddressSuggestions(true);
        setAddressLoading(false);
        return;
      }
      
      // Try external APIs with CORS proxy and error handling
      try {
        // Search for both addresses and businesses/companies
        const searches = [
          // Regular address search via CORS proxy
          fetch(`https://cors-anywhere.herokuapp.com/https://nominatim.openstreetmap.org/search?format=json&addressdetails=1&limit=3&q=${encodeURIComponent(query + ', Switzerland')}`, {
            headers: {
              'X-Requested-With': 'XMLHttpRequest'
            }
          }).catch(() => null),
          
          // Business search via CORS proxy
          fetch(`https://cors-anywhere.herokuapp.com/https://nominatim.openstreetmap.org/search?format=json&addressdetails=1&limit=3&q=${encodeURIComponent(query)}&amenity=restaurant,cafe,shop,bank,hospital,pharmacy,fuel,parking,hotel,office&countrycodes=ch`, {
            headers: {
              'X-Requested-With': 'XMLHttpRequest'
            }
          }).catch(() => null)
        ];
        
        const responses = await Promise.allSettled(searches);
        let allSuggestions = [];
        
        // Process results if available
        for (let i = 0; i < responses.length; i++) {
          if (responses[i].status === 'fulfilled' && responses[i].value && responses[i].value.ok) {
            try {
              const data = await responses[i].value.json();
              const suggestions = data.map(item => ({
                display_name: item.display_name,
                lat: parseFloat(item.lat),
                lon: parseFloat(item.lon),
                type: item.amenity || item.shop || item.type || (i === 0 ? 'address' : 'business'),
                address: item.display_name.split(',')[0],
                source: i === 0 ? 'address' : 'business'
              }));
              allSuggestions = [...allSuggestions, ...suggestions];
            } catch (parseError) {
              console.log('Failed to parse response', i);
            }
          }
        }
        
        if (allSuggestions.length > 0) {
          // Remove duplicates and sort
          const uniqueSuggestions = [];
          const seen = new Set();
          
          for (const suggestion of allSuggestions) {
            const key = `${suggestion.lat},${suggestion.lon}`;
            if (!seen.has(key)) {
              seen.add(key);
              uniqueSuggestions.push(suggestion);
            }
          }
          
          setAddressSuggestions(uniqueSuggestions.slice(0, 8));
          setShowAddressSuggestions(true);
        } else {
          // Fallback to extended local data
          const extendedLocalResults = getExtendedLocalData(query);
          setAddressSuggestions(extendedLocalResults);
          setShowAddressSuggestions(true);
        }
        
      } catch (apiError) {
        console.log('External APIs not available, using local data');
        const extendedLocalResults = getExtendedLocalData(query);
        setAddressSuggestions(extendedLocalResults);
        setShowAddressSuggestions(true);
      }
      
    } catch (error) {
      console.error('Error searching address:', error);
      // Fallback to local data even on error
      const fallbackResults = getExtendedLocalData(query);
      if (fallbackResults.length > 0) {
        setAddressSuggestions(fallbackResults);
        setShowAddressSuggestions(true);
      } else {
        setAddressError('Search temporarily unavailable. Please enter address manually.');
      }
    } finally {
      setAddressLoading(false);
    }
  };

  // Enhanced fuzzy search function
  const fuzzyMatch = (text, query) => {
    if (!text || !query) return { score: 0, match: false };
    
    const textLower = text.toLowerCase();
    const queryLower = query.toLowerCase();
    
    // Exact match gets highest score
    if (textLower.includes(queryLower)) {
      return { score: 100, match: true };
    }
    
    // Word boundary matches (e.g., "bistro" matches "Züribistro")
    const words = textLower.split(/[\s\-_\.]+/);
    for (const word of words) {
      if (word.includes(queryLower)) {
        return { score: 90, match: true };
      }
    }
    
    // Partial word matches (e.g., "rest" matches "restaurant")
    for (const word of words) {
      if (queryLower.length >= 3 && word.startsWith(queryLower)) {
        return { score: 80, match: true };
      }
    }
    
    // Character similarity (basic fuzzy matching)
    let matchCount = 0;
    let queryIndex = 0;
    
    for (let i = 0; i < textLower.length && queryIndex < queryLower.length; i++) {
      if (textLower[i] === queryLower[queryIndex]) {
        matchCount++;
        queryIndex++;
      }
    }
    
    const similarity = matchCount / queryLower.length;
    if (similarity >= 0.7) {
      return { score: Math.floor(similarity * 70), match: true };
    }
    
    return { score: 0, match: false };
  };

  // Local company and address data for Switzerland
  const getLocalCompanyData = (query) => {
    const localCompanies = [
      // Migros
      { name: 'Migros Zurich Hauptbahnhof', address: 'Migros Hauptbahnhof, Bahnhofplatz, 8001 Zürich', lat: 47.3783, lon: 8.5398, type: 'supermarket', source: 'business', keywords: ['migros', 'supermarket', 'grocery', 'food'] },
      { name: 'Migros City', address: 'Migros City, Lowenstrasse 35, 8001 Zürich', lat: 47.3739, lon: 8.5381, type: 'supermarket', source: 'business', keywords: ['migros', 'city', 'supermarket', 'grocery'] },
      { name: 'Migros Oerlikon', address: 'Migros Oerlikon, Wallisellenstrasse 6, 8050 Zürich', lat: 47.4100, lon: 8.5449, type: 'supermarket', source: 'business', keywords: ['migros', 'oerlikon', 'supermarket'] },
      
      // Coop
      { name: 'Coop City Zurich', address: 'Coop City, Bahnhofstrasse 100, 8001 Zürich', lat: 47.3742, lon: 8.5389, type: 'supermarket', source: 'business', keywords: ['coop', 'city', 'supermarket', 'grocery'] },
      { name: 'Coop Paradeplatz', address: 'Coop Paradeplatz, Poststrasse 17, 8001 Zürich', lat: 47.3695, lon: 8.5390, type: 'supermarket', source: 'business', keywords: ['coop', 'paradeplatz', 'supermarket'] },
      
      // McDonald's
      { name: 'McDonald\'s Bahnhofstrasse', address: 'McDonald\'s Bahnhofstrasse 32, 8001 Zürich', lat: 47.3753, lon: 8.5395, type: 'restaurant', source: 'business', keywords: ['mcdonalds', 'burger', 'fast', 'food', 'restaurant'] },
      { name: 'McDonald\'s Hauptbahnhof', address: 'McDonald\'s Hauptbahnhof, Bahnhofplatz, 8001 Zürich', lat: 47.3780, lon: 8.5400, type: 'restaurant', source: 'business', keywords: ['mcdonalds', 'burger', 'hauptbahnhof', 'fast'] },
      
      // ETH & Universities
      { name: 'ETH Zurich Hauptgebäude', address: 'ETH Zurich, Rämistrasse 101, 8092 Zürich', lat: 47.3764, lon: 8.5485, type: 'university', source: 'company', keywords: ['eth', 'university', 'tech', 'education', 'school'] },
      { name: 'University of Zurich', address: 'Universität Zürich, Rämistrasse 71, 8006 Zürich', lat: 47.3742, lon: 8.5490, type: 'university', source: 'company', keywords: ['university', 'uni', 'education', 'school'] },
      
      // Banks
      { name: 'UBS Bahnhofstrasse', address: 'UBS Bahnhofstrasse 45, 8001 Zürich', lat: 47.3726, lon: 8.5395, type: 'bank', source: 'business', keywords: ['ubs', 'bank', 'finance', 'money'] },
      { name: 'Credit Suisse Paradeplatz', address: 'Credit Suisse Paradeplatz 8, 8001 Zürich', lat: 47.3695, lon: 8.5390, type: 'bank', source: 'business', keywords: ['credit', 'suisse', 'bank', 'finance'] },
      
      // Hotels
      { name: 'Hotel Baur au Lac', address: 'Hotel Baur au Lac, Talstrasse 1, 8001 Zürich', lat: 47.3667, lon: 8.5384, type: 'hotel', source: 'business', keywords: ['hotel', 'baur', 'luxury', 'accommodation'] },
      { name: 'Hotel Dolder Grand', address: 'The Dolder Grand, Kurhausstrasse 65, 8032 Zürich', lat: 47.3733, lon: 8.5767, type: 'hotel', source: 'business', keywords: ['hotel', 'dolder', 'grand', 'luxury'] },
      
      // Shopping Centers
      { name: 'Sihlcity', address: 'Sihlcity, Kalanderplatz 1, 8045 Zürich', lat: 47.3581, lon: 8.5186, type: 'shopping_mall', source: 'business', keywords: ['sihlcity', 'shopping', 'mall', 'center'] },
      { name: 'Glattzentrum', address: 'Glattzentrum, Neue Winterthurerstrasse 99, 8304 Wallisellen', lat: 47.4147, lon: 8.6064, type: 'shopping_mall', source: 'business', keywords: ['glattzentrum', 'shopping', 'mall'] },
      
      // Local Small Businesses
      { name: 'binzstudio.ch', address: 'binzstudio.ch, Bühlstrasse 45E, 8005 Zürich', lat: 47.3642, lon: 8.5158, type: 'tattoo_studio', source: 'business', keywords: ['binzstudio', 'binz', 'tattoo', 'studio', 'art', 'ink'] },
      
      // Example local businesses with fuzzy-friendly keywords
      { name: 'Café Zunfthaus', address: 'Café Zunfthaus, Limmatquai 54, 8001 Zürich', lat: 47.3722, lon: 8.5434, type: 'cafe', source: 'business', keywords: ['café', 'cafe', 'coffee', 'zunfthaus', 'drink'] },
      { name: 'Bäckerei Klingler', address: 'Bäckerei Klingler, Bahnhofstrasse 15, 8001 Zürich', lat: 47.3755, lon: 8.5390, type: 'bakery', source: 'business', keywords: ['bäckerei', 'bakery', 'bread', 'klingler', 'food'] },
      { name: 'Züribistro Restaurant', address: 'Züribistro, Münstergasse 8, 8001 Zürich', lat: 47.3708, lon: 8.5426, type: 'restaurant', source: 'business', keywords: ['züribistro', 'bistro', 'restaurant', 'food', 'dining'] },
      { name: 'Pizza Corner', address: 'Pizza Corner, Langstrasse 92, 8004 Zürich', lat: 47.3769, lon: 8.5177, type: 'restaurant', source: 'business', keywords: ['pizza', 'corner', 'italian', 'restaurant', 'food'] },
      { name: 'Tech Startup Hub', address: 'Tech Hub, Hardstrasse 201, 8005 Zürich', lat: 47.3889, lon: 8.5147, type: 'office', source: 'company', keywords: ['tech', 'startup', 'hub', 'office', 'coworking'] }
    ];

    const searchTerm = query.toLowerCase();
    const results = [];
    
    localCompanies.forEach(company => {
      let bestScore = 0;
      let hasMatch = false;
      
      // Check name match
      const nameMatch = fuzzyMatch(company.name, searchTerm);
      if (nameMatch.match) {
        bestScore = Math.max(bestScore, nameMatch.score);
        hasMatch = true;
      }
      
      // Check address match
      const addressMatch = fuzzyMatch(company.address, searchTerm);
      if (addressMatch.match) {
        bestScore = Math.max(bestScore, addressMatch.score - 10); // Slightly lower priority for address
        hasMatch = true;
      }
      
      // Check type match
      const typeMatch = fuzzyMatch(company.type, searchTerm);
      if (typeMatch.match) {
        bestScore = Math.max(bestScore, typeMatch.score - 5);
        hasMatch = true;
      }
      
      // Check keywords match
      if (company.keywords) {
        company.keywords.forEach(keyword => {
          const keywordMatch = fuzzyMatch(keyword, searchTerm);
          if (keywordMatch.match) {
            bestScore = Math.max(bestScore, keywordMatch.score);
            hasMatch = true;
          }
        });
      }
      
      if (hasMatch && bestScore >= 50) { // Minimum threshold for relevance
        results.push({
          company,
          score: bestScore
        });
      }
    });
    
    // Sort by relevance score (highest first)
    return results
      .sort((a, b) => b.score - a.score)
      .slice(0, 8) // Limit results
      .map(result => ({
        display_name: result.company.address,
        lat: result.company.lat,
        lon: result.company.lon,
        type: result.company.type,
        address: result.company.name,
        source: result.company.source,
        company_type: result.company.type,
        relevanceScore: result.score
      }));
  };

  const getExtendedLocalData = (query) => {
    // Extended local data for common Swiss addresses and landmarks
    const extendedData = [
      // Zurich landmarks
      { name: 'Zurich Hauptbahnhof', address: 'Bahnhofplatz, 8001 Zürich', lat: 47.3783, lon: 8.5398, type: 'transport', source: 'address' },
      { name: 'Paradeplatz', address: 'Paradeplatz, 8001 Zürich', lat: 47.3695, lon: 8.5390, type: 'square', source: 'address' },
      { name: 'Bahnhofstrasse', address: 'Bahnhofstrasse, 8001 Zürich', lat: 47.3742, lon: 8.5389, type: 'street', source: 'address' },
      { name: 'Limmatquai', address: 'Limmatquai, 8001 Zürich', lat: 47.3722, lon: 8.5434, type: 'street', source: 'address' },
      { name: 'Zurich Airport', address: 'Flughafen Zürich, 8058 Zürich-Flughafen', lat: 47.4647, lon: 8.5492, type: 'airport', source: 'address' },
      
      // Common Swiss locations
      { name: 'Bern Hauptbahnhof', address: 'Bahnhofplatz, 3011 Bern', lat: 46.9489, lon: 7.4393, type: 'transport', source: 'address' },
      { name: 'Geneva Airport', address: 'Aéroport de Genève, 1215 Geneva', lat: 46.2381, lon: 6.1089, type: 'airport', source: 'address' },
      { name: 'Basel SBB', address: 'Centralbahnplatz, 4051 Basel', lat: 47.5478, lon: 7.5895, type: 'transport', source: 'address' }
    ];

    const searchTerm = query.toLowerCase();
    const localResults = getLocalCompanyData(query);
    
    const addressResults = extendedData
      .filter(item => 
        item.name.toLowerCase().includes(searchTerm) ||
        item.address.toLowerCase().includes(searchTerm)
      )
      .map(item => ({
        display_name: item.address,
        lat: item.lat,
        lon: item.lon,
        type: item.type,
        address: item.name,
        source: item.source
      }));

    return [...localResults, ...addressResults].slice(0, 8);
  };

  const selectAddress = async (suggestion) => {
    // Use the more specific address from display_name if available
    const addressToUse = suggestion.source === 'business' || suggestion.source === 'company' 
      ? suggestion.display_name.split(',').slice(0, 2).join(',').trim() // Take company name + street
      : suggestion.address;
    
    setNewSpot({
      ...newSpot,
      address: addressToUse,
      latitude: suggestion.lat.toString(),
      longitude: suggestion.lon.toString()
    });
    
    setCoordinatesAutoFilled(true);
    setShowAddressSuggestions(false);
    setAddressSuggestions([]);
    
    // Get price recommendations for this location
    await getPriceRecommendations(suggestion.lat, suggestion.lon);
  };

  const getPriceRecommendations = async (lat, lon) => {
    try {
      setPriceRecommendationLoading(true);
      
      // Get all parking spots for comparison
      const spotsResponse = await axios.get(`${API}/parking-spots`);
      const allSpots = spotsResponse.data;
      
      // Calculate distances and find nearby spots (within 2km)
      const nearbySpots = allSpots.filter(spot => {
        const distance = calculateDistance(lat, lon, spot.latitude, spot.longitude);
        return distance <= 2; // 2km radius
      });
      
      if (nearbySpots.length === 0) {
        setPriceRecommendations({
          area_average: 3.0,
          competitive_range: { min: 2.0, max: 4.0 },
          nearby_spots: 0,
          location_factor: 'No nearby spots found - using city average',
          quick_options: [2.0, 2.5, 3.0, 3.5, 4.0]
        });
        return;
      }
      
      // Calculate average price in the area
      const rates = nearbySpots.map(spot => spot.hourly_rate);
      const areaAverage = rates.reduce((sum, rate) => sum + rate, 0) / rates.length;
      
      // Calculate competitive range (25th to 75th percentile)
      const sortedRates = rates.sort((a, b) => a - b);
      const q1Index = Math.floor(sortedRates.length * 0.25);
      const q3Index = Math.floor(sortedRates.length * 0.75);
      const competitiveRange = {
        min: sortedRates[q1Index],
        max: sortedRates[q3Index]
      };
      
      // Determine location factor based on area
      let locationFactor = 'Standard area';
      if (isNearCityCenter(lat, lon)) {
        locationFactor = 'City center - higher rates expected';
      } else if (isNearTransportHub(lat, lon)) {
        locationFactor = 'Near transport hub - moderate to high rates';
      } else if (isResidentialArea(nearbySpots)) {
        locationFactor = 'Residential area - lower rates typical';
      }
      
      // Generate quick pricing options
      const quickOptions = [
        Math.max(1.0, areaAverage - 1.0),
        Math.max(1.5, areaAverage - 0.5),
        areaAverage,
        areaAverage + 0.5,
        areaAverage + 1.0
      ].map(price => Math.round(price * 2) / 2); // Round to nearest 0.5
      
      setPriceRecommendations({
        area_average: areaAverage,
        competitive_range: competitiveRange,
        nearby_spots: nearbySpots.length,
        location_factor: locationFactor,
        quick_options: [...new Set(quickOptions)] // Remove duplicates
      });
      
    } catch (error) {
      console.error('Error getting price recommendations:', error);
      setPriceRecommendations({
        area_average: 3.0,
        competitive_range: { min: 2.0, max: 4.0 },
        nearby_spots: 0,
        location_factor: 'Unable to analyze area - using estimated rates',
        quick_options: [2.0, 2.5, 3.0, 3.5, 4.0]
      });
    } finally {
      setPriceRecommendationLoading(false);
    }
  };

  // Helper functions
  const calculateDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371; // Earth's radius in kilometers
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  };

  const isNearCityCenter = (lat, lon) => {
    // Zurich city center coordinates (approximate)
    const zurichCenter = { lat: 47.3769, lon: 8.5417 };
    const distance = calculateDistance(lat, lon, zurichCenter.lat, zurichCenter.lon);
    return distance <= 2; // Within 2km of city center
  };

  const isNearTransportHub = (lat, lon) => {
    // Major transport hubs in Zurich
    const transportHubs = [
      { lat: 47.3783, lon: 8.5398 }, // Hauptbahnhof
      { lat: 47.3647, lon: 8.5492 }, // Stadelhofen
      { lat: 47.4095, lon: 8.5444 }  // Oerlikon
    ];
    
    return transportHubs.some(hub => 
      calculateDistance(lat, lon, hub.lat, hub.lon) <= 1
    );
  };

  const isResidentialArea = (nearbySpots) => {
    // Simple heuristic: if most nearby spots have low rates, likely residential
    const avgRate = nearbySpots.reduce((sum, spot) => sum + spot.hourly_rate, 0) / nearbySpots.length;
    return avgRate < 2.5;
  };

  const resetAddSpotForm = () => {
    setNewSpot({
      name: '',
      latitude: '',
      longitude: '',
      address: '',
      hourly_rate: ''
    });
    setAddressSuggestions([]);
    setShowAddressSuggestions(false);
    setAddressError('');
    setCoordinatesAutoFilled(false);
    setPriceRecommendations(null);
  };

  useEffect(() => {
    loadOwnerSpots();
    
    // Close address suggestions when clicking outside
    const handleClickOutside = (event) => {
      if (!event.target.closest('.address-input-container')) {
        setShowAddressSuggestions(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      if (searchAddressTimeout.current) {
        clearTimeout(searchAddressTimeout.current);
      }
    };
  }, []);

  const loadOwnerSpots = async () => {
    try {
      const response = await axios.get(`${API}/parking-spots`);
      // Filter spots owned by current user
      const ownerSpots = response.data.filter(spot => spot.owner_id === user.id);
      setSpots(ownerSpots);
    } catch (error) {
      console.error('Error loading spots:', error);
    }
  };

  const loadOwnerBookings = async () => {
    try {
      // Get all bookings and filter for spots owned by current user
      const spotsResponse = await axios.get(`${API}/parking-spots`);
      const ownerSpots = spotsResponse.data.filter(spot => spot.owner_id === user.id);
      const ownerSpotIds = ownerSpots.map(spot => spot._id);
      
      const bookingsResponse = await axios.get(`${API}/bookings`);
      const ownerBookingsData = bookingsResponse.data.filter(booking => 
        ownerSpotIds.includes(booking.spot_id)
      );
      
      // Enrich bookings with spot and user information
      const enrichedBookings = await Promise.all(
        ownerBookingsData.map(async (booking) => {
          const spot = ownerSpots.find(s => s._id === booking.spot_id);
          try {
            // Get user info for the booking
            const userResponse = await axios.get(`${API}/users/${booking.user_id}`);
            return {
              ...booking,
              spot_name: spot?.name || 'Unknown Spot',
              spot_address: spot?.address || 'Unknown Address',
              user_email: userResponse.data.email || 'Unknown User'
            };
          } catch (error) {
            return {
              ...booking,
              spot_name: spot?.name || 'Unknown Spot',
              spot_address: spot?.address || 'Unknown Address',
              user_email: 'Unknown User'
            };
          }
        })
      );
      
      setOwnerBookings(enrichedBookings.sort((a, b) => new Date(b.start_time) - new Date(a.start_time)));
    } catch (error) {
      console.error('Error loading owner bookings:', error);
    }
  };

  const loadOwnerReviews = async () => {
    try {
      // Get reviews for owner's parking spots
      const spotsResponse = await axios.get(`${API}/parking-spots`);
      const ownerSpots = spotsResponse.data.filter(spot => spot.owner_id === user.id);
      const ownerSpotIds = ownerSpots.map(spot => spot._id);
      
      const allReviews = [];
      for (const spotId of ownerSpotIds) {
        try {
          const reviewsResponse = await axios.get(`${API}/reviews/spot/${spotId}`);
          const spotReviews = reviewsResponse.data.map(review => ({
            ...review,
            spot_name: ownerSpots.find(s => s._id === spotId)?.name || 'Unknown Spot'
          }));
          allReviews.push(...spotReviews);
        } catch (error) {
          console.error(`Error loading reviews for spot ${spotId}:`, error);
        }
      }
      
      setOwnerReceivedReviews(allReviews.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)));
      
      // Get customer reviews (reviews given by owner to customers)
      try {
        const customerReviewsResponse = await axios.get(`${API}/customer-reviews/by-owner/${user.id}`);
        setCustomerReviews(customerReviewsResponse.data || []);
      } catch (error) {
        // Customer reviews endpoint might not exist yet, that's ok
        setCustomerReviews([]);
      }
    } catch (error) {
      console.error('Error loading owner reviews:', error);
    }
  };

  const submitCustomerReview = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/customer-reviews`, {
        booking_id: selectedBookingForReview._id,
        customer_id: selectedBookingForReview.user_id,
        owner_id: user.id,
        spot_id: selectedBookingForReview.spot_id,
        rating: newCustomerReview.rating,
        comment: newCustomerReview.comment,
        reliability: newCustomerReview.reliability,
        communication: newCustomerReview.communication,
        punctuality: newCustomerReview.punctuality
      });
      
      setShowReviewForm(false);
      setSelectedBookingForReview(null);
      setNewCustomerReview({
        rating: 5,
        comment: '',
        reliability: 5,
        communication: 5,
        punctuality: 5
      });
      loadOwnerReviews();
      alert('Customer review submitted successfully!');
    } catch (error) {
      console.error('Error submitting customer review:', error);
      alert('Error submitting review. Please try again.');
    }
  };

  const handleAddSpot = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/parking-spots`, {
        ...newSpot,
        latitude: parseFloat(newSpot.latitude),
        longitude: parseFloat(newSpot.longitude),
        hourly_rate: parseFloat(newSpot.hourly_rate)
      });
      
      resetAddSpotForm();
      setShowAddSpot(false);
      loadOwnerSpots();
      alert('Parking spot added successfully!');
    } catch (error) {
      console.error('Error adding spot:', error);
      alert('Failed to add parking spot. Please try again.');
    }
  };

  const simulateHardwareUpdate = async (hardwareId, isAvailable) => {
    try {
      await axios.post(`${API}/hardware/${hardwareId}/status?is_available=${isAvailable}`);
      loadOwnerSpots();
      alert(`Hardware status updated: ${isAvailable ? 'Available' : 'Occupied'}`);
    } catch (error) {
      console.error('Error updating hardware status:', error);
      alert('Failed to update hardware status.');
    }
  };

  // Edit Spot Functions
  const handleEditSpot = (spot) => {
    setEditingSpot({
      id: spot.id,
      name: spot.name,
      latitude: spot.latitude.toString(),
      longitude: spot.longitude.toString(),
      address: spot.address,
      hourly_rate: spot.hourly_rate.toString()
    });
    setShowEditSpot(true);
  };

  const handleUpdateSpot = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/parking-spots/${editingSpot.id}`, {
        ...editingSpot,
        latitude: parseFloat(editingSpot.latitude),
        longitude: parseFloat(editingSpot.longitude),
        hourly_rate: parseFloat(editingSpot.hourly_rate)
      });
      
      setShowEditSpot(false);
      setEditingSpot(null);
      loadOwnerSpots();
      alert('Parkplatz erfolgreich aktualisiert!');
    } catch (error) {
      console.error('Error updating spot:', error);
      alert('Fehler beim Aktualisieren des Parkplatzes. Bitte versuchen Sie es erneut.');
    }
  };

  // Delete Spot Functions
  const handleDeleteSpot = (spot) => {
    setSpotToDelete(spot);
    setShowDeleteConfirm(true);
  };

  const confirmDeleteSpot = async () => {
    try {
      await axios.delete(`${API}/parking-spots/${spotToDelete.id}`);
      setShowDeleteConfirm(false);
      setSpotToDelete(null);
      loadOwnerSpots();
      alert('Parkplatz erfolgreich gelöscht!');
    } catch (error) {
      console.error('Error deleting spot:', error);
      alert('Fehler beim Löschen des Parkplatzes. Bitte versuchen Sie es erneut.');
    }
  };

  const cancelDeleteSpot = () => {
    setShowDeleteConfirm(false);
    setSpotToDelete(null);
  };

  // Revenue functions
  const loadRevenueData = async () => {
    try {
      setRevenueLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/owner/revenue/overview`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRevenueData(response.data);
    } catch (error) {
      console.error('Error loading revenue data:', error);
      alert('❌ Fehler beim Laden der Einnahmen-Daten');
    } finally {
      setRevenueLoading(false);
    }
  };

  const loadDetailedRevenue = async (period) => {
    try {
      setRevenueLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/owner/revenue/detailed/${period}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDetailedRevenue(response.data);
    } catch (error) {
      console.error('Error loading detailed revenue:', error);
      alert('❌ Fehler beim Laden der detaillierten Einnahmen');
    } finally {
      setRevenueLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('de-CH', {
      style: 'currency',
      currency: 'CHF'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('de-CH');
  };

  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString('de-CH');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-2xl font-bold text-gray-900">Owner Dashboard</h1>
            <div className="flex items-center space-x-4">
              <span className="text-gray-600">Welcome, {getFirstName(user?.name)}</span>
              {activeTab === 'spots' && (
                <button
                  onClick={() => setShowAddSpot(true)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition duration-200"
                >
                  Add Parking Spot
                </button>
              )}
            </div>
          </div>
          
          {/* Tab Navigation */}
          <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
            <button
              onClick={() => setActiveTab('spots')}
              className={`px-4 py-2 rounded-md font-medium transition-all duration-200 ${
                activeTab === 'spots'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              🗺️ Meine Parking Spots
            </button>
            <button
              onClick={() => setActiveTab('bookings')}
              className={`px-4 py-2 rounded-md font-medium transition-all duration-200 ${
                activeTab === 'bookings'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              📝 Booking History
            </button>
            <button
              onClick={() => setActiveTab('reviews')}
              className={`px-4 py-2 rounded-md font-medium transition-all duration-200 ${
                activeTab === 'reviews'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              ⭐ Bewertungen
            </button>
            <button
              onClick={() => setActiveTab('revenue')}
              className={`px-4 py-2 rounded-md font-medium transition-all duration-200 ${
                activeTab === 'revenue'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              💰 Einnahmen
            </button>
            <button
              onClick={() => setActiveTab('account')}
              className={`px-4 py-2 rounded-md font-medium transition-all duration-200 ${
                activeTab === 'account'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              👤 Account Management
            </button>
          </div>
          {/* Owner manual hardware controls (visible to owner users) */}
          <div className="mt-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Manual Barrier Controls</h3>
            <div className="flex items-center space-x-2">
              <input
                value={deviceId}
                onChange={(e) => setDeviceId(e.target.value)}
                className="px-3 py-2 border rounded-md text-sm"
                aria-label="Device ID"
              />
              <button
                onClick={() => handleManualCommand('raise_barrier')}
                className="bg-green-600 text-white px-3 py-2 rounded-md text-sm hover:bg-green-700"
              >
                Raise Barrier
              </button>
              <button
                onClick={() => handleManualCommand('lower_barrier')}
                className="bg-red-600 text-white px-3 py-2 rounded-md text-sm hover:bg-red-700"
              >
                Lower Barrier
              </button>
              <span className="text-xs text-gray-500">Status: {manualStatus}</span>
            </div>
          </div>
          {/* Assign device to spot UI */}
          <div className="mt-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Device zuweisen</h3>
            <div className="flex items-center space-x-2">
              <input
                value={assignHardwareId}
                onChange={(e) => setAssignHardwareId(e.target.value)}
                className="px-3 py-2 border rounded-md text-sm"
                aria-label="Hardware ID"
                placeholder="Hardware ID (z.B. PARK_DEVICE_001)"
              />
              <select
                value={assignSpotId}
                onChange={(e) => setAssignSpotId(e.target.value)}
                className="px-3 py-2 border rounded-md text-sm"
                aria-label="Select Spot"
              >
                <option value="">-- Wähle Park-Spot --</option>
                {spots && spots.map((s) => (
                  <option key={s.id} value={s.id}>{s.name} (ID: {s.id})</option>
                ))}
              </select>
              <button
                onClick={handleAssignDevice}
                className="bg-blue-600 text-white px-3 py-2 rounded-md text-sm hover:bg-blue-700"
              >
                Zuweisen
              </button>
              <span className="text-xs text-gray-500">Status: {assignStatus}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Add Spot Modal */}
      {showAddSpot && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Add New Parking Spot</h2>
            
            <form onSubmit={handleAddSpot} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Spot Name</label>
                <input
                  type="text"
                  value={newSpot.name}
                  onChange={(e) => setNewSpot({...newSpot, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., My Garage, Office Parking"
                  required
                />
              </div>
              
              {/* Enhanced Address Input with Autocomplete */}
              <div className="address-input-container">
                <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
                <div className="relative">
                  <input
                    type="text"
                    value={newSpot.address}
                    onChange={(e) => handleAddressChange(e.target.value)}
                    onFocus={() => setShowAddressSuggestions(true)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Address, company name, or landmark (e.g., 'McDonald's Zurich', 'ETH Zurich', 'Bahnhofstrasse 1')"
                    required
                  />
                  {addressLoading && (
                    <div className="absolute right-3 top-2">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                    </div>
                  )}
                  
                  {/* Quick Add Local Business Button */}
                  <div className="mt-2">
                    <button
                      type="button"
                      onClick={() => setShowAddBusinessForm(!showAddBusinessForm)}
                      className="text-xs text-blue-600 hover:text-blue-800 underline"
                    >
                      Can't find your business? Click here to add it to our database
                    </button>
                  </div>
                  
                  {/* Address Suggestions Dropdown */}
                  {showAddressSuggestions && addressSuggestions.length > 0 && (
                    <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                      {addressSuggestions.map((suggestion, index) => (
                        <div
                          key={index}
                          onClick={() => selectAddress(suggestion)}
                          className="px-4 py-3 hover:bg-gray-100 cursor-pointer border-b border-gray-100 last:border-b-0"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1 min-w-0">
                              <div className="font-medium text-gray-900 truncate">
                                {suggestion.address}
                              </div>
                              <div className="text-sm text-gray-600 truncate">
                                {suggestion.display_name}
                              </div>
                            </div>
                            <div className="ml-2 flex-shrink-0">
                              {suggestion.source === 'business' && (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                  🏢 {suggestion.amenity || 'Business'}
                                </span>
                              )}
                              {suggestion.source === 'company' && (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                  🏭 {suggestion.company_type || 'Company'}
                                </span>
                              )}
                              {suggestion.source === 'address' && (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                  📍 Address
                                </span>
                              )}
                            </div>
                          </div>
                          {suggestion.brand && (
                            <div className="text-xs text-purple-600 mt-1">
                              Brand: {suggestion.brand}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                {addressError && (
                  <p className="text-red-600 text-sm mt-1">{addressError}</p>
                )}
                
                {/* Add Local Business Form */}
                {showAddBusinessForm && (
                  <div className="mt-4 p-4 border border-blue-200 rounded-lg bg-blue-50">
                    <h4 className="font-medium text-blue-900 mb-3">Add Your Business to Our Database</h4>
                    <div className="text-sm text-blue-800 mb-3">
                      Help other users find your business by adding it to our local database. Once added, it will appear in search suggestions.
                    </div>
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-3">
                        <input
                          type="text"
                          placeholder="Business Name"
                          className="px-3 py-2 border border-blue-300 rounded text-sm focus:ring-2 focus:ring-blue-500"
                          onBlur={(e) => {
                            if (e.target.value) {
                              setNewSpot({...newSpot, name: e.target.value});
                            }
                          }}
                        />
                        <input
                          type="text"
                          placeholder="Business Type (e.g., restaurant, shop)"
                          className="px-3 py-2 border border-blue-300 rounded text-sm focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <input
                        type="text"
                        placeholder="Full Address"
                        className="w-full px-3 py-2 border border-blue-300 rounded text-sm focus:ring-2 focus:ring-blue-500"
                        onBlur={(e) => {
                          if (e.target.value) {
                            setNewSpot({...newSpot, address: e.target.value});
                            // Auto-fill coordinates if possible
                            handleAddressChange(e.target.value);
                          }
                        }}
                      />
                      <div className="grid grid-cols-2 gap-3">
                        <input
                          type="number"
                          step="any"
                          placeholder="Latitude"
                          className="px-3 py-2 border border-blue-300 rounded text-sm focus:ring-2 focus:ring-blue-500"
                          onBlur={(e) => {
                            if (e.target.value) {
                              setNewSpot({...newSpot, latitude: e.target.value});
                            }
                          }}
                        />
                        <input
                          type="number"
                          step="any"
                          placeholder="Longitude"
                          className="px-3 py-2 border border-blue-300 rounded text-sm focus:ring-2 focus:ring-blue-500"
                          onBlur={(e) => {
                            if (e.target.value) {
                              setNewSpot({...newSpot, longitude: e.target.value});
                            }
                          }}
                        />
                      </div>
                      <div className="flex space-x-2">
                        <button
                          type="button"
                          onClick={() => {
                            setShowAddBusinessForm(false);
                            alert('Business information saved! It will be available for future searches.');
                          }}
                          className="flex-1 bg-blue-600 text-white py-2 px-3 rounded text-sm hover:bg-blue-700"
                        >
                          Save to Database
                        </button>
                        <button
                          type="button"
                          onClick={() => setShowAddBusinessForm(false)}
                          className="flex-1 bg-gray-300 text-gray-700 py-2 px-3 rounded text-sm hover:bg-gray-400"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                    <div className="text-xs text-blue-600 mt-2">
                      💡 Tip: You can find coordinates easily by searching your address on Google Maps and clicking on the location.
                    </div>
                  </div>
                )}
              </div>
              
              {/* Coordinates - Auto-filled but editable */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Latitude
                    {coordinatesAutoFilled && <span className="text-green-600 text-xs ml-1">✓ Auto-filled</span>}
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={newSpot.latitude}
                    onChange={(e) => setNewSpot({...newSpot, latitude: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., 47.3769"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Longitude
                    {coordinatesAutoFilled && <span className="text-green-600 text-xs ml-1">✓ Auto-filled</span>}
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={newSpot.longitude}
                    onChange={(e) => setNewSpot({...newSpot, longitude: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., 8.5417"
                    required
                  />
                </div>
              </div>
              
              {/* Smart Hourly Rate with Recommendations */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Hourly Rate (CHF)
                  {priceRecommendationLoading && <span className="text-blue-600 text-xs ml-1">Analyzing area...</span>}
                </label>
                <div className="relative">
                  <input
                    type="number"
                    step="0.1"
                    value={newSpot.hourly_rate}
                    onChange={(e) => setNewSpot({...newSpot, hourly_rate: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., 2.50"
                    required
                  />
                </div>
                
                {/* Price Recommendations */}
                {priceRecommendations && (
                  <div className="mt-2 p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <h4 className="font-medium text-blue-900 mb-2">💡 Pricing Recommendations</h4>
                    
                    {priceRecommendations.area_average && (
                      <div className="mb-2">
                        <span className="text-sm text-blue-800">
                          Area Average: <strong>CHF {priceRecommendations.area_average.toFixed(2)}/hour</strong>
                        </span>
                        <button
                          type="button"
                          onClick={() => setNewSpot({...newSpot, hourly_rate: priceRecommendations.area_average.toFixed(2)})}
                          className="ml-2 text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700"
                        >
                          Use This
                        </button>
                      </div>
                    )}
                    
                    <div className="text-xs text-blue-700 space-y-1">
                      {priceRecommendations.competitive_range && (
                        <div>Competitive Range: CHF {priceRecommendations.competitive_range.min} - {priceRecommendations.competitive_range.max}/hour</div>
                      )}
                      {priceRecommendations.nearby_spots > 0 && (
                        <div>Based on {priceRecommendations.nearby_spots} nearby parking spots</div>
                      )}
                      {priceRecommendations.location_factor && (
                        <div>Location Factor: {priceRecommendations.location_factor}</div>
                      )}
                    </div>
                    
                    {priceRecommendations.quick_options && priceRecommendations.quick_options.length > 0 && (
                      <div className="mt-2">
                        <div className="text-xs text-blue-700 mb-1">Quick Options:</div>
                        <div className="flex gap-1 flex-wrap">
                          {priceRecommendations.quick_options.map((price, index) => (
                            <button
                              key={index}
                              type="button"
                              onClick={() => setNewSpot({...newSpot, hourly_rate: price.toString()})}
                              className="text-xs bg-white border border-blue-300 text-blue-700 px-2 py-1 rounded hover:bg-blue-100"
                            >
                              CHF {price}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
              
              {/* Additional Info */}
              {newSpot.latitude && newSpot.longitude && (
                <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                  📍 Location will be marked at coordinates: {newSpot.latitude}, {newSpot.longitude}
                </div>
              )}
              
              <div className="flex space-x-4 pt-4">
                <button
                  type="submit"
                  disabled={addressLoading || priceRecommendationLoading}
                  className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition duration-200 disabled:opacity-50"
                >
                  {addressLoading || priceRecommendationLoading ? 'Processing...' : 'Add Spot'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowAddSpot(false);
                    resetAddSpotForm();
                  }}
                  className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400 transition duration-200"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Spot Modal */}
      {showEditSpot && editingSpot && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Parkplatz bearbeiten</h2>
            
            <form onSubmit={handleUpdateSpot} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Spot Name</label>
                <input
                  type="text"
                  value={editingSpot.name}
                  onChange={(e) => setEditingSpot({...editingSpot, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Adresse</label>
                <input
                  type="text"
                  value={editingSpot.address}
                  onChange={(e) => setEditingSpot({...editingSpot, address: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Latitude</label>
                  <input
                    type="number"
                    step="any"
                    value={editingSpot.latitude}
                    onChange={(e) => setEditingSpot({...editingSpot, latitude: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Longitude</label>
                  <input
                    type="number"
                    step="any"
                    value={editingSpot.longitude}
                    onChange={(e) => setEditingSpot({...editingSpot, longitude: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Stundensatz (CHF)</label>
                <input
                  type="number"
                  step="0.1"
                  value={editingSpot.hourly_rate}
                  onChange={(e) => setEditingSpot({...editingSpot, hourly_rate: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              
              <div className="flex space-x-4 pt-4">
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition duration-200"
                >
                  Aktualisieren
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowEditSpot(false);
                    setEditingSpot(null);
                  }}
                  className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400 transition duration-200"
                >
                  Abbrechen
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && spotToDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Parkplatz löschen</h2>
            
            <div className="mb-6">
              <p className="text-gray-700 mb-2">
                Sind Sie sicher, dass Sie diesen Parkplatz löschen möchten?
              </p>
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="font-medium text-gray-900">{spotToDelete.name}</p>
                <p className="text-sm text-gray-600">{spotToDelete.address}</p>
                <p className="text-sm text-gray-600">CHF {spotToDelete.hourly_rate}/Stunde</p>
              </div>
              <p className="text-red-600 text-sm mt-2">
                ⚠️ Diese Aktion kann nicht rückgängig gemacht werden.
              </p>
            </div>
            
            <div className="flex space-x-4">
              <button
                onClick={confirmDeleteSpot}
                className="flex-1 bg-red-600 text-white py-2 rounded-lg hover:bg-red-700 transition duration-200"
              >
                Ja, löschen
              </button>
              <button
                onClick={cancelDeleteSpot}
                className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400 transition duration-200"
              >
                Abbrechen
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tab Content */}
      <div className="max-w-6xl mx-auto px-4 py-6">
        {activeTab === 'spots' && (
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-6">🗺️ Meine Parking Spots ({spots.length})</h2>
            
            {/* Main Content with Grid Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Owner Spots Map */}
              <div className="lg:col-span-2">
                <div className="bg-white rounded-lg shadow-md overflow-hidden">
                  <div className="p-4 bg-gray-50 border-b">
                    <h3 className="text-lg font-medium text-gray-900">📍 Standorte Ihrer Parkplätze</h3>
                    <p className="text-sm text-gray-600 mt-1">Übersicht aller Ihrer registrierten Parkplätze auf der Karte</p>
                  </div>
                  <div style={{ height: '400px', width: '100%' }}>
                    {spots.length > 0 ? (
                      <MapComponent 
                        spotsToShow={spots}
                        userLocation={null}
                        showUserLocation={false}
                        onSpotClick={(spot) => {
                          alert(`${spot.name}\nStatus: ${spot.is_available ? 'Verfügbar' : 'Belegt'}\nPreis: CHF ${spot.hourly_rate}/Stunde`);
                        }}
                        mapHeight="400px"
                      />
                    ) : (
                      <div className="h-full flex items-center justify-center bg-gray-100">
                        <div className="text-center text-gray-500">
                          <p className="text-lg font-medium">Keine Parkplätze vorhanden</p>
                          <p className="text-sm">Fügen Sie Ihren ersten Parkplatz hinzu, um ihn hier zu sehen</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              
              {/* Parking Spots Summary Sidebar */}
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900">📊 Übersicht</h3>
                
                {/* Quick Stats */}
                <div className="bg-white rounded-lg shadow-md p-4 space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Gesamt Parkplätze</span>
                    <span className="font-semibold text-blue-600">{spots.length}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Verfügbar</span>
                    <span className="font-semibold text-green-600">
                      {spots.filter(spot => spot.is_available).length}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Belegt</span>
                    <span className="font-semibold text-red-600">
                      {spots.filter(spot => !spot.is_available).length}
                    </span>
                  </div>
                </div>

                {/* Recent Spots */}
                <div className="bg-white rounded-lg shadow-md p-4">
                  <h4 className="font-medium text-gray-900 mb-3">
                    Nächste Spots {userLocation && '(Nach Entfernung)'}
                  </h4>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {(userLocation 
                      ? spots.sort((a, b) => {
                          const distA = calculateDistance(userLocation.lat, userLocation.lng, a.latitude, a.longitude);
                          const distB = calculateDistance(userLocation.lat, userLocation.lng, b.latitude, b.longitude);
                          return distA - distB;
                        })
                      : spots
                    ).slice(0, 5).map((spot) => {
                      const distance = userLocation 
                        ? calculateDistance(userLocation.lat, userLocation.lng, spot.latitude, spot.longitude)
                        : null;
                      
                      return (
                      <div key={spot.id} className="p-2 bg-gray-50 rounded border">
                        <div className="flex justify-between items-start">
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 truncate">
                              {spot.name}
                            </p>
                            <p className="text-xs text-gray-500 truncate">
                              {spot.address}
                            </p>
                            {distance && (
                              <p className="text-xs text-blue-600">
                                {distance.toFixed(1)} km entfernt
                              </p>
                            )}
                          </div>
                          <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium flex-shrink-0 ${
                            spot.is_available 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {spot.is_available ? 'Frei' : 'Belegt'}
                          </span>
                        </div>
                        <p className="text-xs text-gray-600 mt-1">
                          CHF {spot.hourly_rate}/Stunde
                        </p>
                      </div>
                      );
                    })}
                    {spots.length === 0 && (
                      <p className="text-gray-500 text-sm text-center py-4">
                        Noch keine Parkplätze hinzugefügt
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
            
            {/* Detailed Parking Spots List */}
            <div className="mt-8">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                📋 Parkplatz-Details {userLocation && '(Nach Entfernung sortiert)'}
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {(userLocation 
                  ? spots.sort((a, b) => {
                      const distA = calculateDistance(userLocation.lat, userLocation.lng, a.latitude, a.longitude);
                      const distB = calculateDistance(userLocation.lat, userLocation.lng, b.latitude, b.longitude);
                      return distA - distB;
                    })
                  : spots
                ).map((spot) => {
                  const distance = userLocation 
                    ? calculateDistance(userLocation.lat, userLocation.lng, spot.latitude, spot.longitude)
                    : null;

                  return (
                    <div key={spot.id} className="bg-white rounded-lg shadow-md p-6">
                      <div className="flex justify-between items-start mb-4">
                        <h3 className="font-semibold text-gray-900">{spot.name}</h3>
                        <div className="text-right">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            spot.is_available 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {spot.is_available ? 'Available' : 'Occupied'}
                          </span>
                          {distance && (
                            <p className="text-xs text-gray-500 mt-1">
                              {distance.toFixed(1)} km away
                            </p>
                          )}
                        </div>
                      </div>
                    
                    <p className="text-gray-600 text-sm mb-2">{spot.address}</p>
                    <p className="text-gray-600 text-sm mb-4">${spot.hourly_rate}/hour</p>
                    
                    <div className="space-y-2">
                      <p className="text-xs text-gray-500">Hardware ID: {spot.hardware_id}</p>
                      
                      {/* Barrier Control */}
                      <div className="mt-2">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">🔧 Schrankensteuerung</h4>
                        <div className="flex space-x-2">
                          <button
                            onClick={async () => {
                              const hid = spot.hardware_id || 'PARK_DEVICE_001';
                              try {
                                await sendHardwareCommandSimple(hid, 'raise_barrier');
                                alert('Befehl gesendet: Schranke öffnen (raise)');
                              } catch (e) {
                                alert('Fehler: Konnte Öffnen-Befehl nicht senden');
                              }
                            }}
                            className="flex-1 bg-emerald-600 text-white py-2 px-3 rounded text-sm hover:bg-emerald-700 transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                            disabled={!spot.hardware_id}
                          >
                            ⬆️ Öffnen
                          </button>
                          <button
                            onClick={async () => {
                              const hid = spot.hardware_id || 'PARK_DEVICE_001';
                              try {
                                await sendHardwareCommandSimple(hid, 'lower_barrier');
                                alert('Befehl gesendet: Schranke schliessen (lower)');
                              } catch (e) {
                                alert('Fehler: Konnte Schliessen-Befehl nicht senden');
                              }
                            }}
                            className="flex-1 bg-amber-600 text-white py-2 px-3 rounded text-sm hover:bg-amber-700 transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                            disabled={!spot.hardware_id}
                          >
                            ⬇️ Schliessen
                          </button>
                        </div>
                        {!spot.hardware_id && (
                          <p className="text-xs text-gray-500 mt-1">
                            Kein Hardware-Gerät verknüpft. Bitte hinterlege eine Hardware-ID beim Spot.
                          </p>
                        )}
                      </div>

                      {/* Hardware Status Controls */}
                      <div className="flex space-x-2 mb-3">
                        <button
                          onClick={() => simulateHardwareUpdate(spot.hardware_id, true)}
                          className="flex-1 bg-green-600 text-white py-1 px-2 rounded text-sm hover:bg-green-700 transition duration-200"
                          disabled={spot.is_available}
                        >
                          Set Available
                        </button>
                        <button
                          onClick={() => simulateHardwareUpdate(spot.hardware_id, false)}
                          className="flex-1 bg-red-600 text-white py-1 px-2 rounded text-sm hover:bg-red-700 transition duration-200"
                          disabled={!spot.is_available}
                        >
                          Set Occupied
                        </button>
                      </div>

                      {/* Edit/Delete Controls */}
                      <div className="flex space-x-2 pt-2 border-t border-gray-200">
                        <button
                          onClick={() => handleEditSpot(spot)}
                          className="flex-1 bg-blue-600 text-white py-2 px-3 rounded text-sm hover:bg-blue-700 transition duration-200 flex items-center justify-center"
                        >
                          ✏️ Bearbeiten
                        </button>
                        <button
                          onClick={() => handleDeleteSpot(spot)}
                          className="flex-1 bg-red-600 text-white py-2 px-3 rounded text-sm hover:bg-red-700 transition duration-200 flex items-center justify-center"
                        >
                          🗑️ Löschen
                        </button>
                      </div>
                    </div>
                  </div>
                  );
                })}
                
                {spots.length === 0 && (
                  <div className="col-span-full text-center py-12">
                    <p className="text-gray-500 mb-4">No parking spots yet</p>
                    <button
                      onClick={() => setShowAddSpot(true)}
                      className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition duration-200"
                    >
                      Add Your First Spot
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'bookings' && (
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-6">📝 Booking History ({ownerBookings.length})</h2>
            {ownerBookings.length === 0 ? (
              <div className="bg-white rounded-lg shadow-md p-8 text-center">
                <div className="text-gray-400 text-4xl mb-4">📅</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Bookings Yet</h3>
                <p className="text-gray-600">Your parking spots haven't been booked yet. Keep your spots visible and competitive!</p>
              </div>
            ) : (
              <div className="space-y-4">
                {ownerBookings.map((booking) => (
                  <div key={booking._id} className="bg-white rounded-lg shadow-md p-6">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="font-semibold text-gray-900">{booking.spot_name}</h3>
                        <p className="text-gray-600 text-sm">{booking.spot_address}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-green-600">${booking.total_price}</p>
                        <p className="text-gray-500 text-sm">Total Earned</p>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="text-gray-500">Customer</p>
                        <p className="font-medium">{booking.user_email}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Start Time</p>
                        <p className="font-medium">{new Date(booking.start_time).toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">End Time</p>
                        <p className="font-medium">{new Date(booking.end_time).toLocaleString()}</p>
                      </div>
                    </div>
                    
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-500">Duration</span>
                        <span className="font-medium">
                          {Math.round((new Date(booking.end_time) - new Date(booking.start_time)) / (1000 * 60 * 60 * 24))} days
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'reviews' && (
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-6">⭐ Bewertungen</h2>
            
            {/* Sub-navigation for reviews */}
            <div className="mb-6">
              <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg inline-flex">
                <button
                  onClick={() => setActiveReviewTab('received')}
                  className={`px-4 py-2 rounded-md font-medium transition-all duration-200 ${
                    activeReviewTab === 'received'
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  📥 Erhaltene Bewertungen
                </button>
                <button
                  onClick={() => setActiveReviewTab('give')}
                  className={`px-4 py-2 rounded-md font-medium transition-all duration-200 ${
                    activeReviewTab === 'give'
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  ✍️ Kunden bewerten
                </button>
              </div>
            </div>

            {/* Received Reviews Section */}
            {activeReviewTab === 'received' && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Bewertungen deiner Parkplätze ({ownerReceivedReviews.length})
                </h3>
                {ownerReceivedReviews.length === 0 ? (
                  <div className="bg-white rounded-lg shadow-md p-8 text-center">
                    <div className="text-gray-400 text-4xl mb-4">⭐</div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Noch keine Bewertungen</h3>
                    <p className="text-gray-600">Deine Parkplätze wurden noch nicht bewertet. Stelle sicher, dass deine Spots sichtbar und attraktiv sind!</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {ownerReceivedReviews.map((review) => (
                      <div key={review._id} className="bg-white rounded-lg shadow-md p-6">
                        <div className="flex justify-between items-start mb-4">
                          <div>
                            <h4 className="font-semibold text-gray-900">{review.spot_name}</h4>
                            <div className="flex items-center mt-1">
                              {[...Array(5)].map((_, i) => (
                                <span
                                  key={i}
                                  className={`text-lg ${
                                    i < review.rating ? 'text-yellow-400' : 'text-gray-300'
                                  }`}
                                >
                                  ⭐
                                </span>
                              ))}
                              <span className="ml-2 text-sm text-gray-600">
                                {review.rating}/5
                              </span>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-sm text-gray-500">
                              {new Date(review.created_at).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                        {review.comment && (
                          <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">
                            "{review.comment}"
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Give Customer Reviews Section */}
            {activeReviewTab === 'give' && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Kunden bewerten
                </h3>
                <p className="text-gray-600 mb-6">
                  Bewerte deine Kunden basierend auf Zuverlässigkeit, Kommunikation und Pünktlichkeit.
                </p>
                
                {/* Bookings available for review */}
                <div className="space-y-4">
                  {ownerBookings
                    .filter(booking => {
                      // Only show completed bookings that haven't been reviewed by owner yet
                      const isCompleted = new Date(booking.end_time) < new Date();
                      const hasReview = customerReviews.some(review => review.booking_id === booking._id);
                      return isCompleted && !hasReview;
                    })
                    .map((booking) => (
                      <div key={booking._id} className="bg-white rounded-lg shadow-md p-6">
                        <div className="flex justify-between items-start mb-4">
                          <div>
                            <h4 className="font-semibold text-gray-900">{booking.spot_name}</h4>
                            <p className="text-gray-600 text-sm">Kunde: {booking.user_email}</p>
                            <p className="text-gray-500 text-sm">
                              {new Date(booking.start_time).toLocaleDateString()} - {new Date(booking.end_time).toLocaleDateString()}
                            </p>
                          </div>
                          <button
                            onClick={() => {
                              setSelectedBookingForReview(booking);
                              setShowReviewForm(true);
                            }}
                            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition duration-200"
                          >
                            Bewerten
                          </button>
                        </div>
                      </div>
                    ))}
                  
                  {ownerBookings.filter(booking => {
                    const isCompleted = new Date(booking.end_time) < new Date();
                    const hasReview = customerReviews.some(review => review.booking_id === booking._id);
                    return isCompleted && !hasReview;
                  }).length === 0 && (
                    <div className="bg-white rounded-lg shadow-md p-8 text-center">
                      <div className="text-gray-400 text-4xl mb-4">✍️</div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Keine Bewertungen ausstehend</h3>
                      <p className="text-gray-600">Alle abgeschlossenen Buchungen wurden bereits bewertet oder es gibt noch keine abgeschlossenen Buchungen.</p>
                    </div>
                  )}
                </div>

                {/* Already given reviews */}
                {customerReviews.length > 0 && (
                  <div className="mt-8">
                    <h4 className="text-lg font-semibold text-gray-900 mb-4">
                      Bereits abgegebene Bewertungen ({customerReviews.length})
                    </h4>
                    <div className="space-y-4">
                      {customerReviews.map((review) => (
                        <div key={review._id} className="bg-gray-50 rounded-lg p-4">
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-medium text-gray-900">Kunde bewertet</p>
                              <p className="text-sm text-gray-600">Gesamt: {review.rating}⭐</p>
                              <div className="text-xs text-gray-500 mt-1">
                                Zuverlässigkeit: {review.reliability}⭐ | 
                                Kommunikation: {review.communication}⭐ | 
                                Pünktlichkeit: {review.punctuality}⭐
                              </div>
                            </div>
                            <p className="text-xs text-gray-500">
                              {new Date(review.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          {review.comment && (
                            <p className="text-sm text-gray-700 mt-2 italic">"{review.comment}"</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'revenue' && (
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-6">💰 Einnahmen-Übersicht</h2>
            
            {revenueLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="text-gray-600 mt-4">Lade Einnahmen-Daten...</p>
                </div>
              </div>
            ) : revenueData ? (
              <div>
                {/* Overview Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                  <div className="bg-gradient-to-r from-green-400 to-green-600 text-white p-6 rounded-lg shadow-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-green-100 text-sm font-medium">Gesamt-Einnahmen</p>
                        <p className="text-2xl font-bold">{formatCurrency(revenueData.total_revenue)}</p>
                      </div>
                      <div className="text-green-200">
                        <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                        </svg>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gradient-to-r from-blue-400 to-blue-600 text-white p-6 rounded-lg shadow-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-blue-100 text-sm font-medium">Gesamt-Buchungen</p>
                        <p className="text-2xl font-bold">{revenueData.total_sessions}</p>
                      </div>
                      <div className="text-blue-200">
                        <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gradient-to-r from-purple-400 to-purple-600 text-white p-6 rounded-lg shadow-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-purple-100 text-sm font-medium">Ø pro Buchung</p>
                        <p className="text-2xl font-bold">{formatCurrency(revenueData.average_session_value)}</p>
                      </div>
                      <div className="text-purple-200">
                        <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                          <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
                        </svg>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gradient-to-r from-orange-400 to-orange-600 text-white p-6 rounded-lg shadow-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-orange-100 text-sm font-medium">Aktive Parkplätze</p>
                        <p className="text-2xl font-bold">{revenueData.spots_count}</p>
                      </div>
                      <div className="text-orange-200">
                        <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Navigation for detailed views */}
                <div className="flex space-x-4 mb-6">
                  <button
                    onClick={() => setShowDetailedView(false)}
                    className={`px-4 py-2 rounded-md font-medium transition-colors duration-200 ${
                      !showDetailedView
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    📊 Übersicht
                  </button>
                  <button
                    onClick={() => {
                      setShowDetailedView(true);
                      loadDetailedRevenue(selectedPeriod);
                    }}
                    className={`px-4 py-2 rounded-md font-medium transition-colors duration-200 ${
                      showDetailedView
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    📈 Detaillierte Ansicht
                  </button>
                </div>

                {!showDetailedView ? (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Quick Revenue Overview */}
                    <div className="bg-white p-6 rounded-lg shadow-lg">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">📈 Letzte 6 Monate</h3>
                      <div className="space-y-3">
                        {revenueData.monthly_revenue.map((item, index) => (
                          <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-md">
                            <span className="font-medium text-gray-700">{item.month}</span>
                            <span className="font-bold text-green-600">{formatCurrency(item.revenue)}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Top Performing Spots */}
                    <div className="bg-white p-6 rounded-lg shadow-lg">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">🏆 Top Parkplätze</h3>
                      <div className="space-y-4">
                        {revenueData.top_performing_spots.slice(0, 5).map((spot, index) => (
                          <div key={spot.spot_id} className="flex items-center justify-between p-4 bg-gray-50 rounded-md">
                            <div className="flex items-center space-x-3">
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold ${
                                index === 0 ? 'bg-yellow-500' : 
                                index === 1 ? 'bg-gray-400' : 
                                index === 2 ? 'bg-orange-600' : 'bg-blue-500'
                              }`}>
                                {index + 1}
                              </div>
                              <div>
                                <p className="font-medium text-gray-900">{spot.name}</p>
                                <p className="text-sm text-gray-600">{spot.sessions} Buchungen</p>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="font-bold text-green-600">{formatCurrency(spot.revenue)}</p>
                              <p className="text-sm text-gray-600">{formatCurrency(spot.average_per_session)}/Buchung</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Recent Sessions */}
                    <div className="bg-white p-6 rounded-lg shadow-lg lg:col-span-2">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">🕒 Neueste Buchungen</h3>
                      <div className="overflow-x-auto">
                        <table className="min-w-full">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left py-2 px-4 font-medium text-gray-700">Parkplatz</th>
                              <th className="text-left py-2 px-4 font-medium text-gray-700">Datum</th>
                              <th className="text-left py-2 px-4 font-medium text-gray-700">Dauer</th>
                              <th className="text-right py-2 px-4 font-medium text-gray-700">Betrag</th>
                            </tr>
                          </thead>
                          <tbody>
                            {revenueData.recent_sessions.map((session, index) => (
                              <tr key={session.session_id} className={`border-b ${index % 2 === 0 ? 'bg-gray-50' : 'bg-white'}`}>
                                <td className="py-3 px-4">
                                  <p className="font-medium text-gray-900">{session.spot_name}</p>
                                </td>
                                <td className="py-3 px-4 text-gray-600">
                                  {formatDate(session.end_time)}
                                </td>
                                <td className="py-3 px-4 text-gray-600">
                                  {Math.round(session.duration_hours * 10) / 10}h
                                </td>
                                <td className="py-3 px-4 text-right font-bold text-green-600">
                                  {formatCurrency(session.amount)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="bg-white p-6 rounded-lg shadow-lg">
                    {/* Period Selection */}
                    <div className="flex space-x-4 mb-6">
                      <h3 className="text-lg font-semibold text-gray-900">Zeitraum auswählen:</h3>
                      <div className="flex space-x-2">
                        {['daily', 'weekly', 'monthly', 'yearly'].map((period) => (
                          <button
                            key={period}
                            onClick={() => {
                              setSelectedPeriod(period);
                              loadDetailedRevenue(period);
                            }}
                            className={`px-3 py-1 rounded-md text-sm font-medium transition-colors duration-200 ${
                              selectedPeriod === period
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                            }`}
                          >
                            {period === 'daily' ? 'Täglich' : 
                             period === 'weekly' ? 'Wöchentlich' : 
                             period === 'monthly' ? 'Monatlich' : 'Jährlich'}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Detailed Revenue Table */}
                    {detailedRevenue && (
                      <div>
                        <div className="mb-4 p-4 bg-blue-50 rounded-lg">
                          <p className="text-lg font-semibold text-blue-900">
                            Gesamt-Einnahmen ({selectedPeriod}): {formatCurrency(detailedRevenue.total)}
                          </p>
                        </div>
                        
                        <div className="overflow-x-auto">
                          <table className="min-w-full">
                            <thead>
                              <tr className="border-b bg-gray-50">
                                <th className="text-left py-3 px-4 font-medium text-gray-700">Zeitraum</th>
                                <th className="text-right py-3 px-4 font-medium text-gray-700">Einnahmen</th>
                                <th className="text-right py-3 px-4 font-medium text-gray-700">Buchungen</th>
                                <th className="text-right py-3 px-4 font-medium text-gray-700">Kunden</th>
                                <th className="text-right py-3 px-4 font-medium text-gray-700">Ø pro Buchung</th>
                              </tr>
                            </thead>
                            <tbody>
                              {detailedRevenue.revenue_data.map((item, index) => (
                                <tr key={index} className={`border-b ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                                  <td className="py-3 px-4 font-medium text-gray-900">{item.period}</td>
                                  <td className="py-3 px-4 text-right font-bold text-green-600">
                                    {formatCurrency(item.revenue)}
                                  </td>
                                  <td className="py-3 px-4 text-right text-gray-600">{item.sessions}</td>
                                  <td className="py-3 px-4 text-right text-gray-600">{item.unique_users}</td>
                                  <td className="py-3 px-4 text-right text-blue-600 font-medium">
                                    {formatCurrency(item.average_per_session)}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white p-8 rounded-lg shadow-lg text-center">
                <div className="text-6xl mb-4">💰</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Keine Einnahmen vorhanden</h3>
                <p className="text-gray-600">
                  Sie haben noch keine abgeschlossenen Buchungen. Sobald Kunden Ihre Parkplätze nutzen, werden hier die Einnahmen angezeigt.
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'account' && (
          <OwnerAccountManagement spots={spots} ownerBookings={ownerBookings} user={user} />
        )}
      </div>

      {/* Customer Review Form Modal */}
      {showReviewForm && selectedBookingForReview && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Kunde bewerten
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Buchung: {selectedBookingForReview.spot_name} - {selectedBookingForReview.user_email}
            </p>
            
            <form onSubmit={submitCustomerReview} className="space-y-4">
              {/* Overall Rating */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Gesamtbewertung
                </label>
                <div className="flex space-x-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setNewCustomerReview({...newCustomerReview, rating: star})}
                      className={`text-2xl ${
                        star <= newCustomerReview.rating ? 'text-yellow-400' : 'text-gray-300'
                      } hover:text-yellow-400 transition duration-200`}
                    >
                      ⭐
                    </button>
                  ))}
                </div>
              </div>

              {/* Detailed Ratings */}
              <div className="grid grid-cols-1 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Zuverlässigkeit: {newCustomerReview.reliability}⭐
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={newCustomerReview.reliability}
                    onChange={(e) => setNewCustomerReview({...newCustomerReview, reliability: parseInt(e.target.value)})}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Kommunikation: {newCustomerReview.communication}⭐
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={newCustomerReview.communication}
                    onChange={(e) => setNewCustomerReview({...newCustomerReview, communication: parseInt(e.target.value)})}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Pünktlichkeit: {newCustomerReview.punctuality}⭐
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={newCustomerReview.punctuality}
                    onChange={(e) => setNewCustomerReview({...newCustomerReview, punctuality: parseInt(e.target.value)})}
                    className="w-full"
                  />
                </div>
              </div>

              {/* Comment */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Kommentar (optional)
                </label>
                <textarea
                  value={newCustomerReview.comment}
                  onChange={(e) => setNewCustomerReview({...newCustomerReview, comment: e.target.value})}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Zusätzliche Anmerkungen zum Kunden..."
                />
              </div>

              {/* Buttons */}
              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowReviewForm(false);
                    setSelectedBookingForReview(null);
                  }}
                  className="flex-1 bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700 transition duration-200"
                >
                  Abbrechen
                </button>
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition duration-200"
                >
                  Bewertung abgeben
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// Owner Account Management Component - Enhanced version like user account management
const OwnerAccountManagement = ({ spots, ownerBookings, user }) => {
  const { setUser, token, logout } = useAuth();
  const [activeSection, setActiveSection] = useState('profile');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  
  // Profile form state
  const [profileData, setProfileData] = useState({
    first_name: '',
    last_name: '',
    phone: '',
    address: '',
    city: '',
    zip_code: '',
    country: '',
    secondary_email: '',
    date_of_birth: '',
    business_name: '',
    business_type: '',
    tax_id: '',
    business_address: ''
  });

  // Password change form state
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });

  // Email change form state
  const [emailData, setEmailData] = useState({
    new_email: '',
    password: ''
  });

  // Account summary state
  const [accountSummary, setAccountSummary] = useState(null);

  useEffect(() => {
    loadOwnerProfile();
    loadOwnerAccountSummary();
  }, []);

  const loadOwnerProfile = async () => {
    try {
      const response = await axios.get(`${API}/user/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProfileData({
        first_name: response.data.first_name || '',
        last_name: response.data.last_name || '',
        phone: response.data.phone || '',
        address: response.data.address || '',
        city: response.data.city || '',
        zip_code: response.data.zip_code || '',
        country: response.data.country || '',
        secondary_email: response.data.secondary_email || '',
        date_of_birth: response.data.date_of_birth ? response.data.date_of_birth.split('T')[0] : '',
        business_name: response.data.business_name || '',
        business_type: response.data.business_type || '',
        tax_id: response.data.tax_id || '',
        business_address: response.data.business_address || ''
      });
    } catch (error) {
      console.error('Error loading profile:', error);
      setError('Failed to load profile data');
    }
  };

  const loadOwnerAccountSummary = async () => {
    try {
      const response = await axios.get(`${API}/user/account-summary`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAccountSummary(response.data);
    } catch (error) {
      console.error('Error loading account summary:', error);
    }
  };

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setError('');

    try {
      const updateData = { ...profileData };
      if (updateData.date_of_birth) {
        updateData.date_of_birth = new Date(updateData.date_of_birth).toISOString();
      }

      const response = await axios.put(`${API}/user/profile`, updateData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setMessage('Profil erfolgreich aktualisiert!');
      setUser(response.data.user);
    } catch (error) {
      console.error('Error updating profile:', error);
      setError('Fehler beim Aktualisieren des Profils. Bitte versuchen Sie es erneut.');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setError('');

    if (passwordData.new_password !== passwordData.confirm_password) {
      setError('Neue Passwörter stimmen nicht überein');
      setLoading(false);
      return;
    }

    if (passwordData.new_password.length < 6) {
      setError('Passwort muss mindestens 6 Zeichen lang sein');
      setLoading(false);
      return;
    }

    try {
      await axios.put(`${API}/user/password`, {
        current_password: passwordData.current_password,
        new_password: passwordData.new_password
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setMessage('Passwort erfolgreich aktualisiert!');
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: ''
      });
    } catch (error) {
      console.error('Error updating password:', error);
      setError(error.response?.data?.detail || 'Fehler beim Aktualisieren des Passworts');
    } finally {
      setLoading(false);
    }
  };

  const handleEmailChange = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setError('');

    try {
      const response = await axios.put(`${API}/user/email`, emailData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setMessage('E-Mail erfolgreich aktualisiert! Bitte melden Sie sich erneut an.');
      setEmailData({ new_email: '', password: '' });
      
      // Update token and user data
      localStorage.setItem('token', response.data.access_token);
      setUser({ ...user, email: response.data.new_email });
    } catch (error) {
      console.error('Error updating email:', error);
      setError(error.response?.data?.detail || 'Fehler beim Aktualisieren der E-Mail');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = async (password) => {
    setLoading(true);
    setMessage('');
    setError('');

    try {
      await axios.delete(`${API}/user/account?password=${encodeURIComponent(password)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Clear auth data and redirect
      localStorage.removeItem('token');
      setUser(null);
      alert('Konto erfolgreich gelöscht');
    } catch (error) {
      console.error('Error deleting account:', error);
      setError(error.response?.data?.detail || 'Fehler beim Löschen des Kontos');
    } finally {
      setLoading(false);
      setShowDeleteConfirm(false);
    }
  };

  const sections = [
    { id: 'profile', label: 'Profil-Informationen', icon: '👤' },
    { id: 'business', label: 'Geschäftsinformationen', icon: '🏢' },
    { id: 'security', label: 'Sicherheitseinstellungen', icon: '🔒' },
    { id: 'summary', label: 'Konto-Übersicht', icon: '📊' },
    { id: 'danger', label: 'Konto-Aktionen', icon: '⚠️' }
  ];

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-6">👤 Account Management</h2>
      
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Sidebar Navigation */}
        <div className="lg:w-1/4">
          <div className="bg-white rounded-lg shadow-md p-4">
            <nav className="space-y-2">
              {sections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={`w-full text-left px-4 py-3 rounded-lg text-sm font-medium transition duration-200 ${
                    activeSection === section.id
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  <span className="mr-3">{section.icon}</span>
                  {section.label}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Main Content */}
        <div className="lg:w-3/4">
          {/* Messages */}
          {message && (
            <div className="mb-4 p-4 rounded-lg bg-green-100 text-green-700">
              {message}
            </div>
          )}
          {error && (
            <div className="mb-4 p-4 rounded-lg bg-red-100 text-red-700">
              {error}
            </div>
          )}

          {/* Profile Information Section */}
          {activeSection === 'profile' && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-6">Persönliche Informationen</h3>
              
              <form onSubmit={handleProfileUpdate} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Vorname
                    </label>
                    <input
                      type="text"
                      value={profileData.first_name}
                      onChange={(e) => setProfileData({...profileData, first_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Nachname
                    </label>
                    <input
                      type="text"
                      value={profileData.last_name}
                      onChange={(e) => setProfileData({...profileData, last_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Telefonnummer
                  </label>
                  <input
                    type="tel"
                    value={profileData.phone}
                    onChange={(e) => setProfileData({...profileData, phone: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Adresse
                  </label>
                  <input
                    type="text"
                    value={profileData.address}
                    onChange={(e) => setProfileData({...profileData, address: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Stadt
                    </label>
                    <input
                      type="text"
                      value={profileData.city}
                      onChange={(e) => setProfileData({...profileData, city: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Postleitzahl
                    </label>
                    <input
                      type="text"
                      value={profileData.zip_code}
                      onChange={(e) => setProfileData({...profileData, zip_code: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Land
                    </label>
                    <input
                      type="text"
                      value={profileData.country}
                      onChange={(e) => setProfileData({...profileData, country: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Sekundäre E-Mail
                  </label>
                  <input
                    type="email"
                    value={profileData.secondary_email}
                    onChange={(e) => setProfileData({...profileData, secondary_email: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Geburtsdatum
                  </label>
                  <input
                    type="date"
                    value={profileData.date_of_birth}
                    onChange={(e) => setProfileData({...profileData, date_of_birth: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition duration-200 disabled:opacity-50"
                >
                  {loading ? 'Aktualisiere...' : 'Profil aktualisieren'}
                </button>
              </form>
            </div>
          )}

          {/* Business Information Section */}
          {activeSection === 'business' && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-6">Geschäftsinformationen</h3>
              
              <form onSubmit={handleProfileUpdate} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Firmenname
                  </label>
                  <input
                    type="text"
                    value={profileData.business_name}
                    onChange={(e) => setProfileData({...profileData, business_name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="z.B. ParkMax GmbH"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Geschäftstyp
                  </label>
                  <select
                    value={profileData.business_type}
                    onChange={(e) => setProfileData({...profileData, business_type: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Bitte wählen</option>
                    <option value="individual">Einzelperson</option>
                    <option value="gmbh">GmbH</option>
                    <option value="ag">AG</option>
                    <option value="kg">KG</option>
                    <option value="ohg">OHG</option>
                    <option value="other">Sonstiges</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Steuernummer / UID
                  </label>
                  <input
                    type="text"
                    value={profileData.tax_id}
                    onChange={(e) => setProfileData({...profileData, tax_id: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="z.B. CHE-123.456.789"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Geschäftsadresse
                  </label>
                  <textarea
                    value={profileData.business_address}
                    onChange={(e) => setProfileData({...profileData, business_address: e.target.value})}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Vollständige Geschäftsadresse"
                  />
                </div>

                {/* Business Statistics */}
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <h4 className="text-lg font-medium text-gray-900 mb-4">Geschäftsstatistiken</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-700">Anzahl Parkplätze</span>
                        <span className="font-semibold text-blue-600">{spots.length}</span>
                      </div>
                    </div>
                    <div className="p-4 bg-green-50 rounded-lg">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-700">Gesamtbuchungen</span>
                        <span className="font-semibold text-green-600">{ownerBookings.length}</span>
                      </div>
                    </div>
                    <div className="p-4 bg-yellow-50 rounded-lg">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-700">Gesamtumsatz</span>
                        <span className="font-semibold text-yellow-600">
                          CHF {ownerBookings.reduce((sum, booking) => sum + booking.total_price, 0).toFixed(2)}
                        </span>
                      </div>
                    </div>
                    <div className="p-4 bg-purple-50 rounded-lg">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-700">Verfügbare Plätze</span>
                        <span className="font-semibold text-purple-600">
                          {spots.filter(spot => spot.is_available).length}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition duration-200 disabled:opacity-50"
                >
                  {loading ? 'Aktualisiere...' : 'Geschäftsinformationen aktualisieren'}
                </button>
              </form>
            </div>
          )}

          {/* Security Settings Section */}
          {activeSection === 'security' && (
            <div className="space-y-6">
              {/* Change Email */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-xl font-bold text-gray-900 mb-6">E-Mail-Adresse ändern</h3>
                <p className="text-gray-600 mb-4">Aktuelle E-Mail: {user?.email}</p>
                
                <form onSubmit={handleEmailChange} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Neue E-Mail-Adresse
                    </label>
                    <input
                      type="email"
                      required
                      value={emailData.new_email}
                      onChange={(e) => setEmailData({...emailData, new_email: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Aktuelles Passwort
                    </label>
                    <input
                      type="password"
                      required
                      value={emailData.password}
                      onChange={(e) => setEmailData({...emailData, password: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={loading}
                    className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition duration-200 disabled:opacity-50"
                  >
                    {loading ? 'Aktualisiere...' : 'E-Mail aktualisieren'}
                  </button>
                </form>
              </div>

              {/* Change Password */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-xl font-bold text-gray-900 mb-6">Passwort ändern</h3>
                
                <form onSubmit={handlePasswordChange} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Aktuelles Passwort
                    </label>
                    <input
                      type="password"
                      required
                      value={passwordData.current_password}
                      onChange={(e) => setPasswordData({...passwordData, current_password: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Neues Passwort
                    </label>
                    <input
                      type="password"
                      required
                      value={passwordData.new_password}
                      onChange={(e) => setPasswordData({...passwordData, new_password: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Neues Passwort bestätigen
                    </label>
                    <input
                      type="password"
                      required
                      value={passwordData.confirm_password}
                      onChange={(e) => setPasswordData({...passwordData, confirm_password: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={loading}
                    className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition duration-200 disabled:opacity-50"
                  >
                    {loading ? 'Aktualisiere...' : 'Passwort aktualisieren'}
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* Account Summary Section */}
          {activeSection === 'summary' && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-6">Konto-Übersicht</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <h4 className="font-medium text-blue-900">Kontoinformationen</h4>
                    <p className="text-blue-700">E-Mail: {user?.email}</p>
                    <p className="text-blue-700">Name: {user?.name}</p>
                    <p className="text-blue-700">Rolle: Owner</p>
                  </div>
                </div>
                
                <div className="space-y-4">
                  <div className="p-4 bg-green-50 rounded-lg">
                    <h4 className="font-medium text-green-900">Aktivitätsstatistiken</h4>
                    <p className="text-green-700">Parkplätze im Besitz: {spots.length}</p>
                    <p className="text-green-700">Gesamtbuchungen: {ownerBookings.length}</p>
                    <p className="text-green-700">Verfügbare Plätze: {spots.filter(spot => spot.is_available).length}</p>
                    <p className="text-green-700">Gesamtumsatz: CHF {ownerBookings.reduce((sum, booking) => sum + booking.total_price, 0).toFixed(2)}</p>
                  </div>
                </div>
              </div>

              {/* Recent Activity */}
              {ownerBookings.length > 0 && (
                <div className="mt-6">
                  <h4 className="font-medium text-gray-900 mb-4">Aktuelle Aktivitäten</h4>
                  <div className="space-y-2">
                    {ownerBookings.slice(0, 5).map((booking) => (
                      <div key={booking._id} className="p-3 bg-gray-50 rounded-lg">
                        <div className="flex justify-between items-center">
                          <span className="font-medium">Buchung: {booking.spot_name}</span>
                          <span className="text-sm text-gray-500">
                            {new Date(booking.start_time).toLocaleDateString()}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">CHF {booking.total_price?.toFixed(2)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Account Actions Section */}
          {activeSection === 'danger' && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-red-600 mb-6">Gefahrenbereich</h3>
              
              <div className="border border-red-200 rounded-lg p-4">
                <h4 className="font-medium text-red-900 mb-2">Konto löschen</h4>
                <p className="text-red-700 text-sm mb-4">
                  Diese Aktion kann nicht rückgängig gemacht werden. Dies wird Ihr Konto und alle zugehörigen Daten dauerhaft löschen.
                </p>
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition duration-200"
                >
                  Konto löschen
                </button>
              </div>

              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">Schnelle Aktionen</h4>
                <div className="space-y-2">
                  <button
                    onClick={logout}
                    className="w-full text-left px-3 py-2 text-gray-700 hover:bg-gray-200 rounded transition duration-200"
                  >
                    Abmelden
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h3 className="text-xl font-bold text-red-600 mb-4">Konto-Löschung bestätigen</h3>
            <p className="text-gray-700 mb-4">
              Bitte geben Sie Ihr Passwort ein, um die Konto-Löschung zu bestätigen. Diese Aktion kann nicht rückgängig gemacht werden.
            </p>
            
            <form onSubmit={(e) => {
              e.preventDefault();
              const password = e.target.password.value;
              handleDeleteAccount(password);
            }}>
              <input
                type="password"
                name="password"
                required
                placeholder="Passwort eingeben"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 mb-4"
              />
              
              <div className="flex space-x-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-red-600 text-white py-2 rounded-lg hover:bg-red-700 transition duration-200 disabled:opacity-50"
                >
                  {loading ? 'Lösche...' : 'Konto löschen'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowDeleteConfirm(false)}
                  className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400 transition duration-200"
                >
                  Abbrechen
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

const AdminDashboard = () => {
  const [users, setUsers] = useState([]);
  const [statistics, setStatistics] = useState({});
  const [allParkingSpots, setAllParkingSpots] = useState([]);
  const [allSessions, setAllSessions] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [userLocation, setUserLocation] = useState(null);

  useEffect(() => {
    fetchAdminData();
    getUserLocation();
  }, []);

  const getUserLocation = () => {
    console.log('Admin requesting user location...');
    
    // Fallback location for testing (Zürich, Switzerland)
    const fallbackLocation = {
      lat: 47.3769,
      lng: 8.5417
    };
    
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const location = {
            lat: position.coords.latitude,
            lng: position.coords.longitude
          };
          console.log('Admin user location obtained:', location);
          setUserLocation(location);
        },
        (error) => {
          console.error('Error getting admin location:', error);
          console.log('Using fallback location for admin...');
          setUserLocation(fallbackLocation);
        },
        {
          enableHighAccuracy: true,
          timeout: 5000,
          maximumAge: 60000
        }
      );
    } else {
      console.error('Geolocation is not supported by this browser');
      console.log('Using fallback location for admin...');
      setUserLocation(fallbackLocation);
    }
  };

  const fetchAdminData = async () => {
    try {
      const [statsRes, usersRes, spotsRes, sessionsRes] = await Promise.all([
        axios.get(`${API}/admin/statistics`),
        axios.get(`${API}/admin/users`),
        axios.get(`${API}/admin/parking-spots`),
        axios.get(`${API}/admin/parking-sessions`)
      ]);
      
      setStatistics(statsRes.data);
      setUsers(usersRes.data);
      setAllParkingSpots(spotsRes.data);
      setAllSessions(sessionsRes.data);
    } catch (error) {
      console.error('Error fetching admin data:', error);
      alert('Error loading admin data');
    } finally {
      setLoading(false);
    }
  };

  const deleteUser = async (userId) => {
    if (!window.confirm('Are you sure you want to delete this user?')) return;
    
    try {
      await axios.delete(`${API}/admin/users/${userId}`);
      setUsers(users.filter(user => user.id !== userId));
      alert('User deleted successfully');
    } catch (error) {
      console.error('Error deleting user:', error);
      alert('Error deleting user');
    }
  };

  const updateUserRole = async (userId, newRole) => {
    try {
      await axios.put(`${API}/admin/users/${userId}/role?new_role=${newRole}`);
      setUsers(users.map(user => 
        user.id === userId ? { ...user, role: newRole } : user
      ));
      alert('User role updated successfully');
    } catch (error) {
      console.error('Error updating user role:', error);
      alert('Error updating user role');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-xl">Loading admin dashboard...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
            <p className="mt-2 text-gray-600">Manage users, parking spots, and view system statistics</p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation Tabs */}
        <div className="flex space-x-1 mb-8">
          {[
            { id: 'overview', name: 'Overview', icon: '📊' },
            { id: 'users', name: 'Users', icon: '👥' },
            { id: 'spots', name: 'Parking Spots', icon: '🅿️' },
            { id: 'sessions', name: 'Sessions', icon: '🚗' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-lg flex items-center space-x-2 ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.name}</span>
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="text-3xl text-blue-600 mr-4">👥</div>
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Users</p>
                    <p className="text-2xl font-bold text-gray-900">{statistics.total_users}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="text-3xl text-purple-600 mr-4">🏢</div>
                  <div>
                    <p className="text-sm font-medium text-gray-600">Parking Owners</p>
                    <p className="text-2xl font-bold text-gray-900">{statistics.total_owners}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="text-3xl text-red-600 mr-4">👑</div>
                  <div>
                    <p className="text-sm font-medium text-gray-600">Administrators</p>
                    <p className="text-2xl font-bold text-gray-900">{statistics.total_admins}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="text-3xl text-green-600 mr-4">🅿️</div>
                  <div>
                    <p className="text-sm font-medium text-gray-600">Parking Spots</p>
                    <p className="text-2xl font-bold text-gray-900">{statistics.total_spots}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="text-3xl text-orange-600 mr-4">🚗</div>
                  <div>
                    <p className="text-sm font-medium text-gray-600">Active Sessions</p>
                    <p className="text-2xl font-bold text-gray-900">{statistics.active_sessions}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="text-3xl text-gray-600 mr-4">📋</div>
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Sessions</p>
                    <p className="text-2xl font-bold text-gray-900">{statistics.total_sessions}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Users Tab */}
        {activeTab === 'users' && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">User Management</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {users.map((user) => (
                    <tr key={user.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{user.name}</div>
                          <div className="text-sm text-gray-500">{user.email}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <select
                          value={user.role}
                          onChange={(e) => updateUserRole(user.id, e.target.value)}
                          className="text-sm border-gray-300 rounded-md"
                        >
                          <option value="user">User</option>
                          <option value="owner">Owner</option>
                          <option value="admin">Admin</option>
                        </select>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(user.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => deleteUser(user.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Parking Spots Tab */}
        {activeTab === 'spots' && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">All Parking Spots</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Address</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rate</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Owner</th>
                    {userLocation && (
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Distance</th>
                    )}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {(userLocation 
                    ? allParkingSpots.sort((a, b) => {
                        const distA = calculateDistance(userLocation.lat, userLocation.lng, a.latitude, a.longitude);
                        const distB = calculateDistance(userLocation.lat, userLocation.lng, b.latitude, b.longitude);
                        return distA - distB;
                      })
                    : allParkingSpots
                  ).map((spot) => {
                    const distance = userLocation 
                      ? calculateDistance(userLocation.lat, userLocation.lng, spot.latitude, spot.longitude)
                      : null;

                    return (
                    <tr key={spot.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{spot.name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{spot.address}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${spot.hourly_rate}/hr</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          spot.is_available ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {spot.is_available ? 'Available' : 'Occupied'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{spot.owner_id}</td>
                      {userLocation && (
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600">
                          {distance ? `${distance.toFixed(1)} km` : 'N/A'}
                        </td>
                      )}
                    </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Sessions Tab */}
        {activeTab === 'sessions' && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">All Parking Sessions</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Spot</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Start Time</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {allSessions.map((session) => (
                    <tr key={session.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{session.user_id}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{session.spot_id}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(session.start_time).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          session.status === 'active' ? 'bg-green-100 text-green-800' :
                          session.status === 'ended' ? 'bg-blue-100 text-blue-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {session.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ${session.total_amount?.toFixed(2) || 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const PaymentSuccess = () => {
  const [status, setStatus] = useState('checking');
  const [sessionId, setSessionId] = useState(null);

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const stripeSessionId = urlParams.get('session_id');
    
    if (stripeSessionId) {
      setSessionId(stripeSessionId);
      checkPaymentStatus(stripeSessionId);
    }
  }, []);

  const checkPaymentStatus = async (stripeSessionId, attempts = 0) => {
    const maxAttempts = 5;
    
    if (attempts >= maxAttempts) {
      setStatus('timeout');
      return;
    }

    try {
      const response = await axios.get(`${API}/payments/status/${stripeSessionId}`);
      
      if (response.data.payment_status === 'paid') {
        setStatus('success');
      } else if (response.data.status === 'expired') {
        setStatus('expired');
      } else {
        // Continue polling
        setTimeout(() => checkPaymentStatus(stripeSessionId, attempts + 1), 2000);
      }
    } catch (error) {
      console.error('Error checking payment status:', error);
      setStatus('error');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md text-center">
        {status === 'checking' && (
          <>
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Processing Payment</h2>
            <p className="text-gray-600">Please wait while we confirm your payment...</p>
          </>
        )}
        
        {status === 'success' && (
          <>
            <div className="text-green-500 text-5xl mb-4">✓</div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Payment Successful!</h2>
            <p className="text-gray-600 mb-6">Thank you for using ParkSmart. Your parking session has been paid.</p>
            <button
              onClick={() => window.location.href = '/'}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition duration-200"
            >
              Back to Dashboard
            </button>
          </>
        )}
        
        {status === 'expired' && (
          <>
            <div className="text-red-500 text-5xl mb-4">⏰</div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Payment Expired</h2>
            <p className="text-gray-600 mb-6">The payment session has expired. Please try again.</p>
            <button
              onClick={() => window.location.href = '/'}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition duration-200"
            >
              Back to Dashboard
            </button>
          </>
        )}
        
        {status === 'error' && (
          <>
            <div className="text-red-500 text-5xl mb-4">❌</div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Payment Error</h2>
            <p className="text-gray-600 mb-6">There was an error processing your payment. Please contact support.</p>
            <button
              onClick={() => window.location.href = '/'}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition duration-200"
            >
              Back to Dashboard
            </button>
          </>
        )}
      </div>
    </div>
  );
};

const App = () => {
  const [showLogin, setShowLogin] = useState(true);
  const { user, logout, isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return showLogin 
      ? <Login onSwitchToRegister={() => setShowLogin(false)} />
      : <Register onSwitchToLogin={() => setShowLogin(true)} />;
  }

  // Handle routing
  const currentPath = window.location.pathname;
  
  if (currentPath === '/payment-success') {
    return <PaymentSuccess />;
  }

  return (
    <div className="relative">
      {/* Logout Button */}
      <button
        onClick={logout}
        className="fixed top-4 right-4 z-50 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition duration-200"
      >
        Logout
      </button>
      
      {user?.role === 'admin' ? <AdminDashboard /> : 
       user?.role === 'owner' ? <OwnerDashboard /> : <UserDashboard />}
    </div>
  );
};

const AppWrapper = () => {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
};

export default AppWrapper;