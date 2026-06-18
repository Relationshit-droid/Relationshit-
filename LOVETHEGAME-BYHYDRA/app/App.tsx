import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { auth } from './src/lib/firebaseClient';
import { onAuthStateChanged } from 'firebase/auth';
import AppNavigator from './src/navigation/AppNavigator';
import LoginAndSignUpScreen from './src/screens/auth/LoginAndSignUp';

const Stack = createStackNavigator();

const AuthenticatedApp = () => {
  return <AppNavigator />;
};

const App = () => {
  const [user, setUser] = useState(null);
  const [checkingAuthState, setCheckingAuthState] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user);
      setCheckingAuthState(false);
    });

    return unsubscribe;
  }, []);

  if (checkingAuthState) {
    // You could return a splash screen here
    return null;
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {user ? (
          <Stack.Screen name="AuthenticatedApp" component={AuthenticatedApp} />
        ) : (
          <Stack.Screen name="LoginAndSignUp" component={LoginAndSignUpScreen} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default App;