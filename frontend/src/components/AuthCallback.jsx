import React, { useEffect } from "react";
import { msalInstance } from "../msalConfig";

const AuthCallback = () => {
  useEffect(() => {
    const handleRedirectResponse = async () => {
      try {
        const response = await msalInstance.handleRedirectPromise();
        if (response) {
          console.log("Login successful!", response);
        }
      } catch (error) {
        console.error("Redirect login failed", error);
      }
    };

    handleRedirectResponse();
  }, []);

  return <h2>Processing login...</h2>;
};

export default AuthCallback;
