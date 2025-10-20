import React, { useState, useRef } from "react";
import axios from "axios";

const ImageUploadComponent = () => {
  const containerRef = useRef(null);
  const [imageFile, setImageFile] = useState(null);
  const [image, setImage] = useState(null);
  const [result, setResult] = useState(null);

  const [hypotheses, setHypotheses] = useState([]);
  const [selectedHypotheses, setSelectedHypotheses] = useState([]);
  const [worthEvidence, setWorthEvidence] = useState([]);

  const [features, setFeatures] = useState([]);
  const [selectedFeature, setSelectedFeature] = useState(null);
  const [highlightArea, setHighlightArea] = useState(null);

  const [loading, setLoading] = useState(false);

  const [zoomScale, setZoomScale] = useState(100);
  const [imagePosition, setImagePosition] = useState({ x: 0, y: 0 });
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);

  const handleImageChange = (e) => {
    setImage(URL.createObjectURL(e.target.files[0]));
    setImageFile(e.target.files[0]);

    setResult(null);
    setHypotheses([]);
    setSelectedHypotheses([]);
    setWorthEvidence([]);
    setFeatures([]);
    setSelectedFeature(null);
    setHighlightArea(null);

    setZoomScale(100);
    setImagePosition({ x: 0, y: 0 });
    setMousePosition({ x: 0, y: 0 });
    setIsDragging(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!imageFile) {
      alert("Please upload an image file");
      return;
    }

    const formData = new FormData();
    formData.append("file", imageFile);
    const { width, height } = containerRef.current.getBoundingClientRect();
    formData.append("container_width", width);
    formData.append("container_height", height);
    setLoading(true);
    try {
      const response = await axios.post("http://localhost:8081/predict/", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      setResult(response.data);

      const sortedHypotheses = response.data.hypotheses.sort((a, b) => b.probability - a.probability);
      setHypotheses(sortedHypotheses);

      setFeatures(response.data.features);
      setSelectedFeature(null);
      setHighlightArea(null);
    } catch (error) {
      console.error("Error submitting the image:", error);
      setResult({ error: "Failed to get the results" });
    } finally {
      setLoading(false);
    }
  };

  const handleFeatureSelect = (featureId) => {
    setSelectedFeature(featureId);
    const feature = features.find((f) => f.feature_id === featureId);
    setHighlightArea(
      feature
        ? {
            x: feature.area_coordinates.x + imagePosition.x,
            y: feature.area_coordinates.y + imagePosition.y,
            width: feature.area_coordinates.width,
            height: feature.area_coordinates.height,
          }
        : null
    );
  };

  const handleHypothesisChange = (hypothesisId, hypothesisName) => {
    const newSelectedHypotheses = selectedHypotheses.includes(hypothesisId)
      ? selectedHypotheses.filter((hypo) => hypo !== hypothesisId)
      : [...selectedHypotheses, hypothesisId];
    setSelectedHypotheses(newSelectedHypotheses);

    const hypothesisWoes = hypotheses.find((h) => h.hypothesis_id === hypothesisId);
    const filteredEvidence = hypothesisWoes.evidence.filter((item) => item.soe !== "Not worth mentioning");
    let newWorthEvidence;
    if (!worthEvidence.some((item) => item.hypothesis_id === hypothesisId)) {
      newWorthEvidence = [
        ...worthEvidence,
        {
          hypothesis_id: hypothesisId,
          hypothesis_name: hypothesisName,
          filtered_evidence: filteredEvidence,
        },
      ];
    } else {
      newWorthEvidence = worthEvidence.filter((item) => item.hypothesis_id !== hypothesisId);
    }
    setWorthEvidence(newWorthEvidence);
  };

  const handleMouseDown = (e) => {
    e.preventDefault();
    if (e.button !== 0) return;
    setIsDragging(true);

    const { top, left, width, height } = e.currentTarget.getBoundingClientRect();
    const cursorX = e.clientX - left;
    const cursorY = e.clientY - top;

    setMousePosition({
      x: cursorX,
      y: cursorY,
    });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;

    const { top, left, width, height } = e.currentTarget.getBoundingClientRect();
    const newCursorX = e.clientX - left;
    const newCursorY = e.clientY - top;

    const element_image_container = document.getElementById("image-container-id");
    const element_image = document.getElementById("image-id");

    const min_x = element_image_container.clientWidth / (zoomScale / 100) - element_image.clientWidth;
    const max_x = 0;
    const min_y = element_image_container.clientHeight / (zoomScale / 100) - element_image.clientHeight;
    const max_y = 0;

    const oldImagePositionX = imagePosition.x;
    const oldImagePositionY = imagePosition.y;
    const newImagePositionX = Math.min(Math.max(imagePosition.x - (mousePosition.x - newCursorX), min_x), max_x);
    const newImagePositionY = Math.min(Math.max(imagePosition.y - (mousePosition.y - newCursorY), min_y), max_y);

    const imageMoveDistance = {
      x: oldImagePositionX - newImagePositionX,
      y: oldImagePositionY - newImagePositionY,
    };

    setImagePosition({
      x: newImagePositionX,
      y: newImagePositionY,
    });

    if (highlightArea) {
      setHighlightArea({
        x: highlightArea.x - imageMoveDistance.x,
        y: highlightArea.y - imageMoveDistance.y,
        width: highlightArea.width,
        height: highlightArea.height,
      });
    }

    setMousePosition({
      x: newCursorX,
      y: newCursorY,
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  return (
    <div className="container mx-auto px-4 py-8 flex flex-col items-center">
      <div className="top-container">
        <div className="left-container">
          {/* Image Upload */}
          {image && (
            <div className="mb-6">
              <label htmlFor="zoom-slider" className="block text-sm font-semibold text-gray-700 mb-2">
                Zoom Level: {zoomScale}%
              </label>
              <input
                id="zoom-slider"
                type="range"
                min="100"
                max="500"
                step="50"
                value={zoomScale}
                onChange={(e) => setZoomScale(e.target.value)}
                className="w-full h-2 bg-gradient-to-r from-indigo-200 to-purple-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
              />
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {/* Zoom Scale Slider */}

            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                Select Image
              </label>
              <input
                type="file"
                onChange={handleImageChange}
                accept="image/*"
                className="block w-full text-base text-gray-700 py-3 px-2 border-2 border-gray-300 rounded-lg cursor-pointer bg-gray-50 file:mr-4 file:py-2.5 file:px-6 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-gradient-to-r file:from-indigo-600 file:to-purple-600 file:text-white hover:file:from-indigo-700 hover:file:to-purple-700 file:cursor-pointer hover:bg-gray-100 transition-colors"
              />
            </div>

            {image && (
              <div
                ref={containerRef}
                id="image-container-id"
                className="image-container"
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
                onMouseDown={handleMouseDown}
                style={{
                  cursor: isDragging ? "grabbing" : "grab",
                }}
              >
                <img
                  id="image-id"
                  src={image}
                  alt="Uploaded"
                  className="image"
                  draggable="true"
                  style={{
                    transform: `scale(${zoomScale / 100}) translate(${imagePosition.x}px, ${imagePosition.y}px)`,
                    transformOrigin: "top left",
                    // transition: isDragging ? "transform 0.3s ease" : "none",
                  }}
                />
                <div
                  className="highlight-box"
                  style={
                    highlightArea
                      ? {
                          position: "absolute",
                          top: `${highlightArea.y * (zoomScale / 100)}px`,
                          left: `${highlightArea.x * (zoomScale / 100)}px`,
                          width: `${highlightArea.width * (zoomScale / 100)}px`,
                          height: `${highlightArea.height * (zoomScale / 100)}px`,
                          border: "3px solid #8b5cf6",
                          backgroundColor: "rgba(139, 92, 246, 0.2)",
                          pointerEvents: "none",
                          borderRadius: "6px",
                          boxShadow: "0 0 20px rgba(139, 92, 246, 0.4)",
                        }
                      : {}
                  }
                />
              </div>
            )}

            <button
              onClick={handleSubmit}
              disabled={loading}
              className="w-full px-6 py-3 mt-6 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-semibold transition duration-200 ease-in-out hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Processing...' : 'Process Image'}
            </button>
          </form>
        </div>

        <div className="right-container mt-6">
          {/* Features */}
          {features.length > 0 && (
            <div>
              <label className="font-bold text-xl text-gray-800 mb-4 block">Select a Feature</label>
              <div className="grid grid-cols-1 gap-2 mt-4">
                {features.map((feature) => (
                  <label
                    key={feature.feature_id}
                    className={`flex items-center p-3 rounded-lg border-2 cursor-pointer transition-all duration-200 ${
                      selectedFeature === feature.feature_id
                        ? 'border-indigo-500 bg-indigo-50 shadow-md'
                        : 'border-gray-200 bg-white hover:border-indigo-300 hover:bg-gray-50'
                    }`}
                  >
                    <input
                      type="radio"
                      name="feature"
                      value={feature.feature_id}
                      checked={selectedFeature === feature.feature_id}
                      onChange={() => handleFeatureSelect(feature.feature_id)}
                      className="w-4 h-4 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                    />
                    <span className="ml-3 text-sm font-medium text-gray-700">{feature.feature_name}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* AI's Recommendation */}
          {result && (
            <div className="mt-6">
              <div className="bg-gradient-to-br from-indigo-100 via-purple-100 to-pink-100 border-2 border-indigo-400 rounded-xl p-5 shadow-lg">
                <h3 className="text-lg font-bold text-indigo-900 mb-3 flex items-center">
                  <svg className="w-6 h-6 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                  AI's Recommendation
                </h3>
                <p className="text-xl font-bold text-gray-900 leading-relaxed bg-white bg-opacity-70 rounded-lg p-4 border-l-4 border-indigo-600">
                  {result.error ? result.error : result.recommendation}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Hypothesis Checkboxes */}
      <div className="mt-8 w-full max-w-6xl">
        {hypotheses.length > 0 && (
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <label className="font-bold text-2xl text-gray-800 mb-6 block">Select Hypotheses</label>
            <div className="grid grid-cols-2 gap-3">
              {hypotheses.map((hypothesis, index) => (
                <label
                  key={index}
                  className={`flex items-center p-4 rounded-xl border-2 cursor-pointer transition-all duration-200 ${
                    selectedHypotheses.includes(hypothesis.hypothesis_id)
                      ? 'border-purple-500 bg-purple-50 shadow-md'
                      : 'border-gray-200 bg-white hover:border-purple-300 hover:bg-gray-50'
                  }`}
                >
                  <input
                    type="checkbox"
                    name="hypotheses"
                    value={hypothesis.hypothesis_id}
                    onChange={() => handleHypothesisChange(hypothesis.hypothesis_id, hypothesis.hypothesis_name)}
                    className="w-5 h-5 text-purple-600 rounded focus:ring-purple-500 cursor-pointer"
                  />
                  <span className="ml-4 flex-1 text-gray-800 font-medium">
                    {hypothesis.hypothesis_name}
                  </span>
                  <span className="ml-2 px-3 py-1 bg-gradient-to-r from-indigo-100 to-purple-100 text-indigo-700 rounded-full text-sm font-semibold">
                    {(hypothesis.probability * 100).toFixed(2)}%
                  </span>
                </label>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-6 mt-8 w-full max-w-7xl px-4">
        {worthEvidence.length > 0
          ? worthEvidence.map((item) => (
              <div
                key={item.hypothesis_id}
                className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6"
              >
                <h3 className="text-2xl font-bold text-gray-800 mb-6 text-center border-b-2 border-indigo-200 pb-3">
                  {item.hypothesis_name}
                </h3>
                {item.filtered_evidence.length > 0 ? (
                  <div className="flex flex-col w-full gap-4">
                    {/* Negative Evidence Section */}
                    {item.filtered_evidence.filter((evidence) => evidence.evidence_type === "negative").length > 0 && (
                      <div className="w-full bg-red-50 rounded-xl p-4 border-2 border-red-200">
                        <h4 className="text-lg font-bold text-red-700 mb-4 flex items-center">
                          <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                          </svg>
                          Evidence Against
                        </h4>
                        {item.filtered_evidence
                          .filter((evidence) => evidence.evidence_type === "negative")
                          .map((evidence) => {
                          const barColor = "#dc2626";
                          const soeLevels = ["Substantial", "Strong", "Decisive"];
                          const selectedIndex = soeLevels.indexOf(evidence.soe);
                          return (
                            <div
                              key={evidence.feature_id}
                              className="mb-3 flex items-center bg-white rounded-lg p-2 shadow-sm"
                            >
                              <h5 className="flex-shrink-0 w-36 text-sm font-medium text-gray-700">{evidence.feature_name}</h5>
                              <div className="flex items-end gap-1 flex-1">
                                {soeLevels.map((level, index) => {
                                  const isColored = index <= selectedIndex;
                                  return (
                                    <div
                                      key={level}
                                      className="relative"
                                      style={{
                                        width: "40px",
                                        height: "12px",
                                        backgroundColor: isColored ? barColor : "#fee2e2",
                                        border: `2px solid ${isColored ? barColor : "#fecaca"}`,
                                        borderRadius: "4px",
                                      }}
                                    >
                                      <span className="absolute -bottom-5 left-0 right-0 text-xs text-center text-gray-600 font-semibold">
                                        {level === "Substantial" ? `-` : level === "Strong" ? `--` : `---`}
                                      </span>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                    {/* Positive Evidence Section */}
                    {item.filtered_evidence.filter((evidence) => evidence.evidence_type === "positive").length > 0 && (
                      <div className="w-full bg-blue-50 rounded-xl p-4 border-2 border-blue-200">
                        <h4 className="text-lg font-bold text-blue-700 mb-4 flex items-center">
                          <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          Evidence For
                        </h4>
                        {item.filtered_evidence
                          .filter((evidence) => evidence.evidence_type === "positive")
                          .map((evidence) => {
                          const barColor = "#2563eb";
                          const soeLevels = ["Substantial", "Strong", "Decisive"];
                          const selectedIndex = soeLevels.indexOf(evidence.soe);
                          return (
                            <div
                              key={evidence.feature_id}
                              className="mb-3 flex items-center bg-white rounded-lg p-2 shadow-sm"
                            >
                              <h5 className="flex-shrink-0 w-36 text-sm font-medium text-gray-700">{evidence.feature_name}</h5>
                              <div className="flex items-end gap-1 flex-1">
                                {soeLevels.map((level, index) => {
                                  const isColored = index <= selectedIndex;
                                  return (
                                    <div
                                      key={level}
                                      className="relative"
                                      style={{
                                        width: "40px",
                                        height: "12px",
                                        backgroundColor: isColored ? barColor : "#dbeafe",
                                        border: `2px solid ${isColored ? barColor : "#bfdbfe"}`,
                                        borderRadius: "4px",
                                      }}
                                    >
                                      <span className="absolute -bottom-5 left-0 right-0 text-xs text-center text-gray-600 font-semibold">
                                        {level === "Substantial" ? `+` : level === "Strong" ? `++` : `+++`}
                                      </span>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-center text-gray-500 italic py-4">There is no worth mentioning evidence.</p>
                )}
              </div>
            ))
          : null}
      </div>

      {loading && (
        <div className="mt-8 flex flex-col items-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-indigo-600"></div>
          <p className="mt-4 text-lg text-gray-700 font-semibold">Processing your image...</p>
        </div>
      )}
    </div>
  );
};

export default ImageUploadComponent;
