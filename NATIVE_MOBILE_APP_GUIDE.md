# 📱 NATIVE MOBILE APP - SMART PARKING
## Von React Web App zu nativer iOS/Android App

*Komplette Anleitung für Mobile App Development*

---

## 🎯 **BESTE OPTIONEN FÜR DEIN PROJEKT**

### **Option 1: React Native (EMPFOHLEN)** ⭐
**Vorteile:**
- ✅ Du kennst bereits React (deine Web-App)
- ✅ 90% Code-Wiederverwendung
- ✅ iOS + Android aus einer Codebase
- ✅ Native Performance
- ✅ Bestehende APIs können weiterverwendet werden

**Nachteile:**
- ❌ Neues Framework lernen
- ❌ Native Module für spezielle Features

### **Option 2: Capacitor (EINFACHSTE)**
**Vorteile:**
- ✅ Deine bestehende React App = Mobile App
- ✅ Minimaler Umbau nötig
- ✅ Native Plugins verfügbar
- ✅ Schnellste Umsetzung

**Nachteile:**
- ❌ Weniger Performance als React Native
- ❌ "Web-App im Container" Gefühl

### **Option 3: Flutter**
**Vorteile:**
- ✅ Sehr gute Performance
- ✅ Google's Framework

**Nachteile:**
- ❌ Komplett neue Sprache (Dart)
- ❌ Backend-Integration neu machen

---

## 🚀 **EMPFEHLUNG: REACT NATIVE SETUP**

### **Warum React Native für dich?**
```javascript
// Dein bestehender React Code:
const ParkingSpots = () => {
  const [spots, setSpots] = useState([]);
  
  useEffect(() => {
    fetch('https://gashis.ch/parking/api/parking-spots.php')
      .then(res => res.json())
      .then(data => setSpots(data));
  }, []);
  
  return (
    <View>
      {spots.map(spot => (
        <ParkingSpot key={spot.id} spot={spot} />
      ))}
    </View>
  );
};

// React Native Version ist 95% identisch!
// Nur <div> wird <View>, <span> wird <Text>
```

---

## 📋 **SCHRITT 1: ENTWICKLUNGSUMGEBUNG SETUP**

### **React Native CLI Installation (macOS)**
```bash
# Node.js & npm (hast du bereits)
# React Native CLI installieren
npm install -g react-native-cli

# iOS Development (Xcode)
xcode-select --install

# Android Development
# Android Studio herunterladen & installieren
# SDK Tools konfigurieren

# React Native Projekt erstellen
npx react-native init SmartParkingApp
cd SmartParkingApp
```

### **Expo Alternative (EINFACHER)**
```bash
# Expo für einfacheren Start
npm install -g @expo/cli

# Neues Projekt
npx create-expo-app SmartParkingApp
cd SmartParkingApp

# Sofort testen
npx expo start
```

---

## 🔧 **SCHRITT 2: BESTEHENDEN CODE PORTIEREN**

### **API Integration (identisch zu Web-App)**
```javascript
// services/api.js
const API_BASE = 'https://gashis.ch/parking/api/';

export const fetchParkingSpots = async () => {
  try {
    const response = await fetch(`${API_BASE}parking-spots.php`);
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

export const updateParkingSpot = async (spotId, status) => {
  try {
    const response = await fetch(`${API_BASE}update-spot.php`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        spot_id: spotId,
        status: status
      })
    });
    return await response.json();
  } catch (error) {
    console.error('Update Error:', error);
    throw error;
  }
};
```

### **Main Screen Conversion**
```javascript
// screens/ParkingMapScreen.js
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Alert
} from 'react-native';
import { fetchParkingSpots } from '../services/api';

const ParkingMapScreen = () => {
  const [spots, setSpots] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadParkingSpots();
    
    // Auto-refresh alle 10 Sekunden
    const interval = setInterval(loadParkingSpots, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadParkingSpots = async () => {
    try {
      const data = await fetchParkingSpots();
      setSpots(data);
    } catch (error) {
      Alert.alert('Fehler', 'Parkplätze konnten nicht geladen werden');
    } finally {
      setLoading(false);
    }
  };

  const renderParkingSpot = ({ item }) => (
    <TouchableOpacity 
      style={[
        styles.spotCard,
        { backgroundColor: item.status === 'free' ? '#4CAF50' : '#F44336' }
      ]}
      onPress={() => showSpotDetails(item)}
    >
      <Text style={styles.spotTitle}>{item.name}</Text>
      <Text style={styles.spotStatus}>
        {item.status === 'free' ? '🟢 FREI' : '🔴 BESETZT'}
      </Text>
      <Text style={styles.spotLocation}>{item.location}</Text>
    </TouchableOpacity>
  );

  const showSpotDetails = (spot) => {
    Alert.alert(
      spot.name,
      `Status: ${spot.status}\nAdresse: ${spot.location}`,
      [
        { text: 'Schließen', style: 'cancel' },
        spot.status === 'free' && { text: 'Reservieren', onPress: () => reserveSpot(spot.id) }
      ].filter(Boolean)
    );
  };

  const reserveSpot = async (spotId) => {
    try {
      await updateParkingSpot(spotId, 'reserved');
      loadParkingSpots(); // Refresh
      Alert.alert('Erfolg', 'Parkplatz reserviert!');
    } catch (error) {
      Alert.alert('Fehler', 'Reservierung fehlgeschlagen');
    }
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <Text>Lade Parkplätze...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.header}>Smart Parking Zürich</Text>
      <FlatList
        data={spots}
        renderItem={renderParkingSpot}
        keyExtractor={(item) => item.id.toString()}
        refreshing={loading}
        onRefresh={loadParkingSpots}
        showsVerticalScrollIndicator={false}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    paddingTop: 50,
  },
  header: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 20,
    color: '#333',
  },
  spotCard: {
    margin: 10,
    padding: 15,
    borderRadius: 10,
    elevation: 3,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  spotTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 5,
  },
  spotStatus: {
    fontSize: 16,
    color: 'white',
    marginBottom: 5,
  },
  spotLocation: {
    fontSize: 14,
    color: 'white',
    opacity: 0.9,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

export default ParkingMapScreen;
```

---

## 🗺️ **SCHRITT 3: KARTEN-INTEGRATION**

### **React Native Maps Setup**
```bash
# Maps Library installieren
npm install react-native-maps

# iOS Setup (in ios/Podfile):
# pod 'react-native-maps', path: '../node_modules/react-native-maps'

# Android Setup automatisch
```

### **Map Component**
```javascript
// components/ParkingMap.js
import React from 'react';
import MapView, { Marker } from 'react-native-maps';
import { View, StyleSheet } from 'react-native';

const ParkingMap = ({ spots }) => {
  const zurichCenter = {
    latitude: 47.3769,
    longitude: 8.5417,
    latitudeDelta: 0.0922,
    longitudeDelta: 0.0421,
  };

  return (
    <MapView style={styles.map} initialRegion={zurichCenter}>
      {spots.map((spot) => (
        <Marker
          key={spot.id}
          coordinate={{
            latitude: parseFloat(spot.latitude),
            longitude: parseFloat(spot.longitude)
          }}
          title={spot.name}
          description={`Status: ${spot.status}`}
          pinColor={spot.status === 'free' ? 'green' : 'red'}
        />
      ))}
    </MapView>
  );
};

const styles = StyleSheet.create({
  map: {
    flex: 1,
  },
});

export default ParkingMap;
```

---

## 🔔 **SCHRITT 4: PUSH NOTIFICATIONS**

### **Expo Notifications Setup**
```bash
# Notifications installieren
npx expo install expo-notifications expo-device expo-constants
```

### **Notification Service**
```javascript
// services/notifications.js
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

export async function registerForPushNotificationsAsync() {
  let token;

  if (Platform.OS === 'android') {
    Notifications.setNotificationChannelAsync('default', {
      name: 'default',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#FF231F7C',
    });
  }

  if (Device.isDevice) {
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;
    
    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }
    
    if (finalStatus !== 'granted') {
      alert('Failed to get push token for push notification!');
      return;
    }
    
    token = await Notifications.getExpoPushTokenAsync({
      projectId: Constants.expoConfig.extra.eas.projectId,
    });
  } else {
    alert('Must use physical device for Push Notifications');
  }

  return token.data;
}

export async function sendParkingNotification(spotName, status) {
  await Notifications.scheduleNotificationAsync({
    content: {
      title: "Smart Parking Update",
      body: `${spotName} ist jetzt ${status === 'free' ? 'frei' : 'besetzt'}!`,
      data: { spotName, status },
    },
    trigger: { seconds: 1 },
  });
}
```

---

## 📍 **SCHRITT 5: GPS & LOCATION FEATURES**

### **Location Services**
```javascript
// services/location.js
import * as Location from 'expo-location';

export async function getCurrentLocation() {
  try {
    const { status } = await Location.requestForegroundPermissionsAsync();
    
    if (status !== 'granted') {
      throw new Error('Permission to access location was denied');
    }

    const location = await Location.getCurrentPositionAsync({});
    return {
      latitude: location.coords.latitude,
      longitude: location.coords.longitude
    };
  } catch (error) {
    console.error('Location Error:', error);
    throw error;
  }
}

export function calculateDistance(lat1, lon1, lat2, lon2) {
  const R = 6371; // Radius der Erde in km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon/2) * Math.sin(dLon/2);
  
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  const distance = R * c; // Distanz in km
  
  return Math.round(distance * 1000); // in Meter
}
```

---

## 🎨 **SCHRITT 6: NATIVE UI KOMPONENTEN**

### **Custom Tab Navigation**
```bash
# Navigation installieren
npm install @react-navigation/native @react-navigation/bottom-tabs
npx expo install react-native-screens react-native-safe-area-context
```

### **App Navigation Setup**
```javascript
// App.js
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';

import ParkingMapScreen from './screens/ParkingMapScreen';
import ParkingListScreen from './screens/ParkingListScreen';
import ProfileScreen from './screens/ProfileScreen';

const Tab = createBottomTabNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <Tab.Navigator
        screenOptions={({ route }) => ({
          tabBarIcon: ({ focused, color, size }) => {
            let iconName;

            if (route.name === 'Karte') {
              iconName = focused ? 'map' : 'map-outline';
            } else if (route.name === 'Liste') {
              iconName = focused ? 'list' : 'list-outline';
            } else if (route.name === 'Profil') {
              iconName = focused ? 'person' : 'person-outline';
            }

            return <Ionicons name={iconName} size={size} color={color} />;
          },
          tabBarActiveTintColor: '#4CAF50',
          tabBarInactiveTintColor: 'gray',
          headerShown: false,
        })}
      >
        <Tab.Screen name="Karte" component={ParkingMapScreen} />
        <Tab.Screen name="Liste" component={ParkingListScreen} />
        <Tab.Screen name="Profil" component={ProfileScreen} />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
```

---

## 🚀 **SCHRITT 7: BUILD & DEPLOYMENT**

### **Expo Build (EINFACH)**
```bash
# EAS Build installieren
npm install -g @expo/cli

# Build konfigurieren
npx expo build:configure

# iOS Build
npx expo build:ios

# Android Build  
npx expo build:android
```

### **App Store Deployment**
```bash
# iOS App Store
# 1. Apple Developer Account ($99/Jahr)
# 2. Bundle ID registrieren
# 3. App Store Connect Setup
# 4. TestFlight für Beta-Tests

# Google Play Store
# 1. Google Play Developer Account ($25 einmalig)
# 2. APK/AAB hochladen
# 3. Store Listing erstellen
# 4. Review Process
```

---

## ✨ **ZUSÄTZLICHE MOBILE FEATURES**

### **Offline Support**
```javascript
// services/offline.js
import AsyncStorage from '@react-native-async-storage/async-storage';

export async function cacheSpots(spots) {
  try {
    await AsyncStorage.setItem('cachedSpots', JSON.stringify(spots));
  } catch (error) {
    console.error('Cache Error:', error);
  }
}

export async function getCachedSpots() {
  try {
    const cached = await AsyncStorage.getItem('cachedSpots');
    return cached ? JSON.parse(cached) : [];
  } catch (error) {
    console.error('Cache Retrieve Error:', error);
    return [];
  }
}
```

### **Background Tasks**
```javascript
// Background refresh für Parkplatz-Updates
import * as BackgroundFetch from 'expo-background-fetch';
import * as TaskManager from 'expo-task-manager';

const BACKGROUND_FETCH_TASK = 'background-fetch';

TaskManager.defineTask(BACKGROUND_FETCH_TASK, async () => {
  try {
    const spots = await fetchParkingSpots();
    await cacheSpots(spots);
    return BackgroundFetch.BackgroundFetchResult.NewData;
  } catch (error) {
    return BackgroundFetch.BackgroundFetchResult.Failed;
  }
});
```

---

## 📊 **ENTWICKLUNGS-TIMELINE**

### **Woche 1: Setup & Basic App**
- [x] React Native Environment
- [x] Basic Navigation
- [x] API Integration
- [x] Simple List View

### **Woche 2: Maps & Location**
- [x] React Native Maps
- [x] GPS Location
- [x] Distance Calculation
- [x] Marker Integration

### **Woche 3: Advanced Features**
- [x] Push Notifications
- [x] Offline Support
- [x] Background Refresh
- [x] User Authentication

### **Woche 4: Polish & Deploy**
- [x] UI/UX Improvements
- [x] Testing auf Devices
- [x] App Store Submission
- [x] Launch! 🚀

---

## 💰 **KOSTEN ÜBERSICHT**

| Service | Kosten |
|---------|--------|
| **Apple Developer** | $99/Jahr (iOS) |
| **Google Play** | $25 einmalig (Android) |
| **Expo EAS Build** | $29/Monat (optional) |
| **Push Notifications** | Kostenlos (Expo) |
| **Maps API** | Kostenlos bis Limit |
| | |
| **Total erste Jahr** | **~$150** |

---

## 🎯 **NEXT STEPS**

1. **Entscheide dich:** React Native oder Capacitor
2. **Development Environment** setup
3. **Bestehende APIs** testen in Mobile App
4. **MVP Version** mit Parkplatz-Liste
5. **Maps Integration** für bessere UX
6. **Beta Testing** mit Freunden/Familie
7. **App Store Launch** 🚀

**Deine bestehende gashis.ch/parking API ist bereits mobile-ready!** Die meiste Arbeit ist UI/UX für Mobile Devices.

---

*Ready to go Mobile? 📱⚡*
