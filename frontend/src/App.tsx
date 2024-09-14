import React, { useState, useRef } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<{ up: number; down: number } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const selectedFile = event.target.files[0];
      setFile(selectedFile);
      setVideoUrl(URL.createObjectURL(selectedFile));
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!file) return;

    setIsLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:8000/process-video/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setResult(response.data);
    } catch (error) {
      console.error('Error processing video:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <h1>Vehicle Detection Demo</h1>
      <form onSubmit={handleSubmit}>
        <input type="file" accept="video/mp4" onChange={handleFileChange} />
        <button type="submit" disabled={!file || isLoading}>
          Process Video
        </button>
      </form>
      {videoUrl && (
        <div className="video-container">
          <video ref={videoRef} src={videoUrl} controls width="100%" />
        </div>
      )}
      {isLoading && <p>Processing video...</p>}
      {result && (
        <div>
          <h2>Results:</h2>
          <p>Vehicles going up: {result.up}</p>
          <p>Vehicles going down: {result.down}</p>
        </div>
      )}
    </div>
  );
}

export default App;