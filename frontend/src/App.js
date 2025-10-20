// App.js
import React from "react";
import "./App.css";
import ImageUploadComponent from "./components/ImageUploadComponent";

function App() {
  return (
    <div className="App">
      {/* Main App Container */}
      <header className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-center py-6 shadow-lg">
        <h1 className="text-4xl font-bold tracking-tight">EvaSkan</h1>
        <p className="text-lg mt-2 text-indigo-100">Upload an image to get started with Evaluative AI.</p>
        <p className="text-sm mt-2 text-indigo-100">For education and research use only.</p>
      </header>

      <main className="flex justify-center items-start min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-8">
        {/* Rendering the main image upload and classification component */}
        <ImageUploadComponent />
      </main>

      <footer className="text-center p-6 text-gray-600 bg-white border-t border-gray-200">
        <p>&copy; {new Date().getFullYear()} EvaSkan. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default App;
