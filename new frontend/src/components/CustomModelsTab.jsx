import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { toast } from 'react-hot-toast';
import { useBlobUrlCleanup } from '../hooks/useBlobUrl';
import blobUrlManager from '../utils/blobUrlManager';
import { useTranslation } from "react-i18next";
import { 
  Upload, 
  Trash2, 
  Heart, 
  Download,
  FileText,
  Calendar,
  HardDrive,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import {
  selectCustomModels,
  selectCustomModelsLoading,
  selectCustomModelsError,
  selectCustomImages,
  selectCustomImagesLoading,
  selectCustomImagesError,
  selectSelectedAvatar,
  selectFavorites,
  addCustomModel,
  removeCustomModel,
  setCustomModelsLoading,
  setCustomModelsError,
  addCustomImage,
  removeCustomImage,
  setCustomImagesLoading,
  setCustomImagesError,
  setSelectedAvatar,
  loadAvatarSettings,
  addFavorite,
} from '../store/avatarSlice';
import { storage } from '../utils/storageUtils';
import indexedDBStorage from '../utils/indexedDBStorage';
import MediaViewer from './MediaViewer';

const CustomModelsTab = () => {
  const { t } = useTranslation();
  const dispatch = useDispatch();
  const customModels = useSelector(selectCustomModels);
  const customImages = useSelector(selectCustomImages);
  const modelsLoading = useSelector(selectCustomModelsLoading);
  const imagesLoading = useSelector(selectCustomImagesLoading);
  const modelsError = useSelector(selectCustomModelsError);
  const imagesError = useSelector(selectCustomImagesError);
  const selectedAvatar = useSelector(selectSelectedAvatar);
  const favorites = useSelector(selectFavorites);

  const [dragOver, setDragOver] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(null);
  const [storageInfo, setStorageInfo] = useState({ usedMB: '0', quotaMB: '1000', availableMB: '1000', percentUsed: '0' });
  const [activeUploadTab, setActiveUploadTab] = useState('models'); // 'models' or 'images'
  const fileInputRef = useRef(null);
  const imageInputRef = useRef(null);

  // Blob URL management for this component
  const { cleanupUrls } = useBlobUrlCleanup('CustomModelsTab');

  // Load storage info on component mount and after operations
  useEffect(() => {
    const loadStorageInfo = async () => {
      console.log('🔄 Loading storage info...');
      const info = await checkStorageSpace();
      console.log('📊 Storage info:', info);
      setStorageInfo(info);
    };

    loadStorageInfo();
  }, [customModels.length, customImages.length]); // Reload when models or images change

  // Add warning about potential data loss (only for unsaved changes)
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (uploadProgress) {
        const message = t('Upload in progress. Leaving now will cancel the upload.');
        e.preventDefault();
        e.returnValue = message;
        return message;
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [uploadProgress, t]);

  // Check IndexedDB storage space (much larger capacity)
  const checkStorageSpace = async () => {
    try {
      const storageInfo = await indexedDBStorage.getStorageInfo();
      return storageInfo;
    } catch (error) {
      console.error('Error checking IndexedDB storage:', error);
      return {
        usedMB: '0',
        quotaMB: '1000',
        availableMB: '1000',
        percentUsed: '0',
        supported: false
      };
    }
  };

  // File validation with IndexedDB (much larger capacity)
  const validateFile = async (file, fileType = 'model') => {
    console.log('🔍 Validating file:', file.name, 'Size:', file.size, 'Type:', fileType);

    let allowedTypes, maxSize, errorMessage;

      if (fileType === 'image') {
      allowedTypes = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'];
      maxSize = 50 * 1024 * 1024; // 50MB for images
        errorMessage = t('Only image files (JPG, PNG, GIF, WebP, BMP) are supported');
    } else {
      allowedTypes = ['.glb'];
      maxSize = 100 * 1024 * 1024; // 100MB for 3D models
        errorMessage = t('Only .glb files are supported');
    }

    if (file.size > maxSize) {
      const maxSizeMB = (maxSize / (1024 * 1024)).toFixed(0);
      throw new Error(`File size must be less than ${maxSizeMB}MB. Try compressing your ${fileType} if it's larger.`);
    }

    const extension = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));
    if (!allowedTypes.includes(extension)) {
      throw new Error(errorMessage);
    }

    console.log('✅ File validation passed');
    return true;
  };

  // Convert file to base64 with timeout
  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      console.log('🔄 Starting FileReader for:', file.name);
      const reader = new FileReader();

      // Add timeout to prevent hanging
      const timeout = setTimeout(() => {
        reader.abort();
        reject(new Error('File reading timed out after 30 seconds'));
      }, 30000);

      reader.onloadstart = () => {
        console.log('🔄 FileReader: Load started');
      };

      reader.onprogress = (e) => {
        if (e.lengthComputable) {
          const progress = (e.loaded / e.total) * 100;
          console.log(`🔄 FileReader: Progress ${progress.toFixed(1)}%`);
        }
      };

      reader.onload = () => {
        clearTimeout(timeout);
        console.log('✅ FileReader: Load complete, result length:', reader.result?.length);
        resolve(reader.result);
      };

      reader.onerror = (error) => {
        clearTimeout(timeout);
        console.error('❌ FileReader: Error:', error);
        reject(error);
      };

      reader.onabort = () => {
        clearTimeout(timeout);
        console.error('❌ FileReader: Aborted');
        reject(new Error('File reading was aborted'));
      };

      reader.readAsDataURL(file);
    });
  };

  // Generate thumbnail (placeholder for now)
  const generateThumbnail = async (file) => {
    // TODO: Implement actual 3D model thumbnail generation
    // For now, return the file data itself as the preview URL
    const base64Data = await fileToBase64(file);
    return base64Data;
  };

  // Handle file upload
  const handleFileUpload = async (files, fileType = 'model') => {
    if (!files || files.length === 0) return;

    console.log('🔄 Starting file upload for:', files.length, 'files', 'Type:', fileType);

    if (fileType === 'image') {
      dispatch(setCustomImagesLoading(true));
      dispatch(setCustomImagesError(null));
    } else {
      dispatch(setCustomModelsLoading(true));
      dispatch(setCustomModelsError(null));
    }

    try {
      for (const file of files) {
        console.log('📁 Processing file:', file.name, 'Size:', file.size);
        setUploadProgress({ fileName: file.name, progress: 0 });

        // Add a small delay to ensure UI updates
        await new Promise(resolve => setTimeout(resolve, 100));

        // Validate file
        console.log('✅ Validating file...');
        await validateFile(file, fileType);
        console.log('✅ File validation complete');

        setUploadProgress({ fileName: file.name, progress: 25 });
        await new Promise(resolve => setTimeout(resolve, 100));

        // Convert to base64
        console.log('🔄 Converting to base64...');
        const base64Data = await fileToBase64(file);
        console.log('✅ Base64 conversion complete, length:', base64Data.length);

        setUploadProgress({ fileName: file.name, progress: 50 });
        await new Promise(resolve => setTimeout(resolve, 100));

        // Generate thumbnail
        console.log('🖼️ Generating thumbnail...');
        const thumbnailUrl = await generateThumbnail(file);
        console.log('✅ Thumbnail generation complete');

        setUploadProgress({ fileName: file.name, progress: 75 });
        await new Promise(resolve => setTimeout(resolve, 100));

        // Create file metadata
        const fileId = `custom_${fileType}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const metadata = {
          id: fileId,
          name: file.name.replace(/\.[^/.]+$/, ""), // Remove extension
          fileName: file.name,
          fileSize: file.size,
          uploadDate: new Date().toISOString(),
          thumbnailUrl,
          type: 'custom',
          isCustom: true,
          mediaType: fileType, // 'model' or 'image'
        };

        console.log('💾 Saving to IndexedDB...', fileId);

        // Save file data to IndexedDB with error handling
        try {
          let success;
          if (fileType === 'image') {
            success = await indexedDBStorage.saveImageFile(fileId, base64Data, metadata);
          } else {
            success = await indexedDBStorage.saveGlbFile(fileId, base64Data, metadata);
          }

          if (!success) {
            throw new Error('Failed to save file to IndexedDB');
          }
          console.log('✅ Successfully saved to IndexedDB');
        } catch (storageError) {
          console.error('❌ IndexedDB storage error:', storageError);
          if (storageError.name === 'QuotaExceededError' || storageError.message.includes('quota')) {
            throw new Error('Storage quota exceeded. Please delete some models or try a smaller file.');
          }
          throw new Error('Failed to save file to storage. Please try again.');
        }

        // Add to Redux store
        console.log('📝 Adding to Redux store...');
        if (fileType === 'image') {
          dispatch(addCustomImage(metadata));
        } else {
          dispatch(addCustomModel(metadata));
        }

        setUploadProgress({ fileName: file.name, progress: 100 });
        await new Promise(resolve => setTimeout(resolve, 100));

        console.log('🎉 Upload complete for:', file.name);
        toast.success(`${file.name} uploaded successfully!`);
      }
    } catch (error) {
      console.error('❌ Upload error:', error);
      if (fileType === 'image') {
        dispatch(setCustomImagesError(error.message));
      } else {
        dispatch(setCustomModelsError(error.message));
      }
      toast.error(`Upload failed: ${error.message}`);
    } finally {
      if (fileType === 'image') {
        dispatch(setCustomImagesLoading(false));
      } else {
        dispatch(setCustomModelsLoading(false));
      }
      setUploadProgress(null);
    }
  };

  // Handle drag and drop
  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const files = Array.from(e.dataTransfer.files);

    // Auto-detect file type based on extension
    const fileType = files.length > 0 && files[0].name.match(/\.(jpg|jpeg|png|gif|webp|bmp)$/i) ? 'image' : 'model';
    handleFileUpload(files, fileType);
  }, []);

  // Handle file input change
  const handleFileInputChange = (e, fileType = 'model') => {
    const files = Array.from(e.target.files);
    handleFileUpload(files, fileType);
    e.target.value = ''; // Reset input
  };

  // Handle media selection (both models and images)
  const handleSelectMedia = async (media) => {
    try {
      let fileData;

      // Load the file data from IndexedDB based on media type
      if (media.mediaType === 'image') {
        fileData = await indexedDBStorage.loadImageFile(media.id);
      } else {
        fileData = await indexedDBStorage.loadGlbFile(media.id);
      }

      if (!fileData) {
        toast.error(`Failed to load ${media.mediaType} file`);
        return;
      }

      let previewUrl = fileData.data;

      // For 3D models, create blob URL for better performance
      if (media.mediaType === 'model') {
        try {
          const base64Data = fileData.data.split(',')[1]; // Remove data:application/octet-stream;base64, prefix
          const binaryString = atob(base64Data);
          const bytes = new Uint8Array(binaryString.length);
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }
          const blob = new Blob([bytes], { type: 'application/octet-stream' });
          previewUrl = blobUrlManager.createBlobUrl(blob, 'CustomModelsTab', {
            mediaId: media.id,
            mediaType: 'model',
            action: 'addToFavorites'
          });
        } catch (error) {
          console.error('🚫 Error creating blob URL for model:', error);
          previewUrl = fileData.data; // Fallback to base64
        }
      }

      // Create avatar object with appropriate data
      // Use the same ID format as favorites (with fav_ prefix) for consistency
      const favoriteId = `fav_${media.id}`;
      const avatarWithData = {
        ...media,
        id: favoriteId, // Use the same ID as the favorite will have
        originalId: media.id, // Keep track of the original media ID
        fileData: fileData.data, // Keep original base64 for storage
        previewUrl, // Use blob URL for 3D models, base64 for images
        isBlobUrl: media.mediaType === 'model', // Flag to clean up later
        isCustomModel: true, // Flag for settings panel
      };

      dispatch(setSelectedAvatar(avatarWithData));
      dispatch(loadAvatarSettings(avatarWithData));

      // Auto-add to favorites for persistence across logout/login
      // Check if this media is already in favorites to avoid duplicates
      const existingFavorite = favorites.find(fav =>
        fav.originalId === media.id || fav.id === favoriteId
      );

      if (!existingFavorite) {
        const favorite = {
          ...media,
          id: favoriteId, // Use the same ID as the selected avatar
          originalId: media.id,
          timestamp: new Date().toISOString(),
          activeTab: 'custom-models',
          previewUrl, // Use blob URL for 3D models, base64 for images
          fileData: fileData.data, // Keep original base64 for storage
          isCustomModel: true,
          // Add default positioning
          gridPosition: { x: 0, y: 0, z: 0 },
          gridRotation: { x: 0, y: 0, z: 0 },
          gridScale: 1,
          pinPosition: { x: 0, y: 0, z: 0 },
          pinRotation: { x: 0, y: 0, z: 0 },
          pinScale: 1,
        };

        dispatch(addFavorite(favorite));

      }

      toast.success(`Selected ${media.name}`);
    } catch (error) {
      console.error('Error selecting media:', error);
      toast.error(`Failed to load ${media.mediaType}`);
    }
  };

  // Handle media deletion (both models and images)
  const handleDeleteMedia = async (media) => {
    if (window.confirm(`Are you sure you want to delete "${media.name}"?`)) {
      try {
        // Delete file from IndexedDB based on media type
        if (media.mediaType === 'image') {
          await indexedDBStorage.deleteImageFile(media.id);
          dispatch(removeCustomImage(media.id));
        } else {
          await indexedDBStorage.deleteGlbFile(media.id);
          dispatch(removeCustomModel(media.id));
        }

        // If this was the selected avatar, clear selection
        if (selectedAvatar?.id === media.id) {
          dispatch(setSelectedAvatar(null));
        }

        // Show storage info after deletion
        const storageInfo = await checkStorageSpace();
        toast.success(`${media.name} deleted. Storage: ${storageInfo.percentUsed}% used`);
      } catch (error) {
        console.error('Error deleting media:', error);
        toast.error(`Failed to delete ${media.mediaType}`);
      }
    }
  };



  // Clear all custom models
  const handleClearAllModels = async () => {
    if (customModels.length === 0) {
      toast.error('No models to delete');
      return;
    }

    if (window.confirm(`Are you sure you want to delete all ${customModels.length} custom models? This cannot be undone.`)) {
      try {
        // Clear all files from IndexedDB
        await indexedDBStorage.clearAllModels();

        // Clear Redux state
        customModels.forEach(model => {
          dispatch(removeCustomModel(model.id));
        });

        // Clear selection if it was a custom model
        if (selectedAvatar?.isCustomModel && selectedAvatar?.mediaType === 'model') {
          dispatch(setSelectedAvatar(null));
        }

        const storageInfo = await checkStorageSpace();
        toast.success(`All custom models deleted. Storage: ${storageInfo.percentUsed}% used`);
      } catch (error) {
        console.error('Error clearing all models:', error);
        toast.error('Failed to clear all models');
      }
    }
  };

  // Clear all custom images
  const handleClearAllImages = async () => {
    if (customImages.length === 0) {
      toast.error('No images to delete');
      return;
    }

    if (window.confirm(`Are you sure you want to delete all ${customImages.length} custom images? This cannot be undone.`)) {
      try {
        // Clear all files from IndexedDB
        await indexedDBStorage.clearAllImages();

        // Clear Redux state
        customImages.forEach(image => {
          dispatch(removeCustomImage(image.id));
        });

        // Clear selection if it was a custom image
        if (selectedAvatar?.isCustomModel && selectedAvatar?.mediaType === 'image') {
          dispatch(setSelectedAvatar(null));
        }

        const storageInfo = await checkStorageSpace();
        toast.success(`All custom images deleted. Storage: ${storageInfo.percentUsed}% used`);
      } catch (error) {
        console.error('Error clearing all images:', error);
        toast.error('Failed to clear all images');
      }
    }
  };

  // Handle add to favorites (both models and images)
  const handleAddToFavorites = async (media) => {
    try {
      let fileData;

      // Load the file data from IndexedDB based on media type
      if (media.mediaType === 'image') {
        fileData = await indexedDBStorage.loadImageFile(media.id);
      } else {
        fileData = await indexedDBStorage.loadGlbFile(media.id);
      }

      if (!fileData) {
        toast.error(`Failed to load ${media.mediaType} file`);
        return;
      }

      let previewUrl = fileData.data;

      // For 3D models, create blob URL for better performance
      if (media.mediaType === 'model') {
        const base64Data = fileData.data.split(',')[1];
        const binaryString = atob(base64Data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        const blob = new Blob([bytes], { type: 'application/octet-stream' });
        previewUrl = blobUrlManager.createBlobUrl(blob, 'CustomModelsTab', {
          mediaId: media.id,
          mediaType: 'model',
          action: 'addToFavorites'
        }) || fileData.data; // Fallback to base64 if blob URL creation fails
      }

      const favorite = {
        ...media,
        id: `fav_${media.id}`,
        originalId: media.id,
        timestamp: new Date().toISOString(),
        activeTab: 'custom-models',
        previewUrl, // Use blob URL for 3D models, base64 for images
        fileData: fileData.data, // Keep original base64 for storage
        isCustomModel: true,
        // Add default positioning
        gridPosition: { x: 0, y: 0, z: 0 },
        gridRotation: { x: 0, y: 0, z: 0 },
        gridScale: 1,
        pinPosition: { x: 0, y: 0, z: 0 },
        pinRotation: { x: 0, y: 0, z: 0 },
        pinScale: 1,
      };

      dispatch(addFavorite(favorite));
      toast.success(`${media.name} added to favorites!`);
    } catch (error) {
      console.error('Error adding to favorites:', error);
      toast.error('Failed to add to favorites');
    }
  };

  // Format file size
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Format date
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  // Get current items based on active tab
  const currentItems = activeUploadTab === 'images' ? customImages : customModels;
  const currentLoading = activeUploadTab === 'images' ? imagesLoading : modelsLoading;
  const currentError = activeUploadTab === 'images' ? imagesError : modelsError;

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">Custom Media</h2>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-sm text-white/60">
              {customModels.length} model{customModels.length !== 1 ? 's' : ''} • {customImages.length} image{customImages.length !== 1 ? 's' : ''}
            </div>
            <div className="text-xs text-white/40">
              Storage: {storageInfo.usedMB}MB / {storageInfo.quotaMB}MB ({storageInfo.percentUsed}%)
            </div>
            <div className="text-xs text-white/30">
              Available: {storageInfo.availableMB}MB
            </div>
          </div>
          {(customModels.length > 0 || customImages.length > 0) && (
            <button
              onClick={activeUploadTab === 'images' ? handleClearAllImages : handleClearAllModels}
              className="px-3 py-1 bg-red-500/20 border border-red-500/30 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors text-sm"
              title={`Delete all custom ${activeUploadTab}`}
            >
              Clear All {activeUploadTab === 'images' ? 'Images' : 'Models'}
            </button>
          )}
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex justify-center space-x-4 mb-6">
        <button
          onClick={() => setActiveUploadTab('models')}
          className={`flex items-center justify-center space-x-2 px-4 py-2 rounded-lg transition-all border ${
            activeUploadTab === 'models'
              ? 'bg-orange-500/30 text-orange-300 border-orange-400/60'
              : 'text-white/90 hover:text-white hover:bg-white/20 bg-white/10 border-white/20'
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>3D Models ({customModels.length})</span>
        </button>
        <button
          onClick={() => setActiveUploadTab('images')}
          className={`flex items-center justify-center space-x-2 px-4 py-2 rounded-lg transition-all border ${
            activeUploadTab === 'images'
              ? 'bg-orange-500/30 text-orange-300 border-orange-400/60'
              : 'text-white/90 hover:text-white hover:bg-white/20 bg-white/10 border-white/20'
          }`}
        >
          <Upload className="w-4 h-4" />
          <span>Images ({customImages.length})</span>
        </button>
      </div>

      {/* Upload Area */}
      <div
        className={`border-2 border-dashed rounded-lg p-6 mb-6 transition-all ${
          dragOver
            ? 'border-orange-400 bg-orange-500/10'
            : 'border-white/20 hover:border-white/40'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="text-center">
          <Upload className="w-8 h-8 text-white/40 mx-auto mb-3" />
          <h3 className="text-lg font-medium text-white mb-2">
            Upload {activeUploadTab === 'images' ? 'Images' : '3D Models'}
          </h3>
          <p className="text-white/60 mb-3">
            {activeUploadTab === 'images'
              ? 'Drag and drop image files here, or click to browse'
              : 'Drag and drop .glb files here, or click to browse'
            }
          </p>
          <div className="flex gap-2 justify-center">
            <button
              onClick={() => {
                if (activeUploadTab === 'images') {
                  imageInputRef.current?.click();
                } else {
                  fileInputRef.current?.click();
                }
              }}
              className="px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg transition-colors text-sm"
              disabled={currentLoading}
            >
              {currentLoading ? 'Uploading...' : `Choose ${activeUploadTab === 'images' ? 'Images' : 'Models'}`}
            </button>
          </div>

          {/* File inputs */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".glb"
            multiple
            onChange={(e) => handleFileInputChange(e, 'model')}
            className="hidden"
          />
          <input
            ref={imageInputRef}
            type="file"
            accept="image/*"
            multiple
            onChange={(e) => handleFileInputChange(e, 'image')}
            className="hidden"
          />
        </div>
      </div>

      {/* Upload Progress */}
      {uploadProgress && (
        <div className="mb-4 p-3 bg-white/5 rounded-lg border border-white/10">
          <div className="flex items-center justify-between mb-2">
            <span className="text-white text-sm">{uploadProgress.fileName}</span>
            <span className="text-white/60 text-sm">{uploadProgress.progress}%</span>
          </div>
          <div className="w-full bg-white/10 rounded-full h-2">
            <div
              className="bg-orange-500 h-2 rounded-full transition-all"
              style={{ width: `${uploadProgress.progress}%` }}
            />
          </div>
        </div>
      )}





      {/* Storage Warning */}
      {parseFloat(storageInfo.percentUsed) > 80 && (
        <div className="mb-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg flex items-center gap-3">
          <AlertCircle className="w-4 h-4 text-yellow-400" />
          <div className="text-yellow-400 text-sm">
            <div>{t("Storage is {{percent}}% full", { percent: storageInfo.percentUsed })}</div>
            <div className="text-xs text-yellow-400/70 mt-1">
              {t("Consider deleting unused models to free up space")}
            </div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {currentError && (
        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-3">
          <AlertCircle className="w-4 h-4 text-red-400" />
          <span className="text-red-400 text-sm">{currentError}</span>
        </div>
      )}

      {/* Media Grid */}
      <div className="flex-1 overflow-y-auto">
        {currentItems.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-white/40">
            {activeUploadTab === 'images' ? (
              <>
                <Upload className="w-16 h-16 mb-4" />
                <p className="text-lg">{t("No custom images uploaded yet")}</p>
                <p className="text-sm">{t("Upload your first image to get started")}</p>
              </>
            ) : (
              <>
                <FileText className="w-16 h-16 mb-4" />
                <p className="text-lg">{t("No custom models uploaded yet")}</p>
                <p className="text-sm">{t("Upload your first .glb model to get started")}</p>
              </>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {currentItems.map((item) => (
              <div
                key={item.id}
                className={`bg-white/5 rounded-lg border overflow-hidden hover:border-orange-500/30 transition-all group cursor-pointer relative ${
                  selectedAvatar?.id === item.id
                    ? 'border-orange-500/50 bg-orange-500/10'
                    : 'border-white/10'
                }`}
                onClick={() => handleSelectMedia(item)}
                style={{ zIndex: 1 }}
              >
                {/* Media Preview */}
                <div className="aspect-square bg-black/20 relative overflow-hidden">
                  {activeUploadTab === 'images' && item.thumbnailUrl ? (
                    <img
                      src={item.thumbnailUrl}
                      alt={item.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      {activeUploadTab === 'images' ? (
                        <>
                          <Upload className="w-8 h-8 text-white/40" />
                          <span className="text-xs text-white/40 ml-2">IMG</span>
                        </>
                      ) : (
                        <>
                          <FileText className="w-8 h-8 text-white/40" />
                          <span className="text-xs text-white/40 ml-2">GLB</span>
                        </>
                      )}
                    </div>
                  )}

                  {/* Hover overlay */}
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100 z-10">
                    <div className="text-white text-sm font-medium">{t("Select")}</div>
                  </div>

                  {/* Delete button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteMedia(item);
                    }}
                    className="absolute top-2 right-2 p-1 bg-black/50 backdrop-blur-sm rounded-full border border-white/20 hover:bg-red-500/50 transition-all opacity-0 group-hover:opacity-100 z-20"
                  >
                    <Trash2 className="w-3 h-3 text-white" />
                  </button>

                  {/* Add to favorites button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAddToFavorites(item);
                    }}
                    className="absolute top-2 left-2 p-1 bg-black/50 backdrop-blur-sm rounded-full border border-white/20 hover:bg-orange-500/50 transition-all opacity-0 group-hover:opacity-100 z-20"
                    title="Add to Favorites"
                  >
                    <Heart className="w-3 h-3 text-white" />
                  </button>
                </div>

                {/* Media Info */}
                <div className="p-3">
                  <h4 className="text-white font-medium text-sm truncate text-center mb-1">
                    {item.name}
                  </h4>
                  <div className="text-xs text-white/60 text-center">
                    {formatFileSize(item.fileSize)}
                  </div>
                  <div className="text-xs text-white/40 text-center">
                    {formatDate(item.uploadDate)}
                  </div>
                  <div className="text-xs text-white/30 text-center">
                    {activeUploadTab === 'images' ? 'Image' : '3D Model'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default CustomModelsTab;
