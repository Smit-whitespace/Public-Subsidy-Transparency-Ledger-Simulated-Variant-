import React, { createContext, useContext } from "react";
import useAuthHook from "../hooks/useAuth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {

  const auth = useAuthHook();

  return (
    <AuthContext.Provider value={auth}>
      {children}
    </AuthContext.Provider>
  );

}

export function useAuth() {

  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;

}