import React, { useState } from 'react';

interface MediaPlayerProps {
    mediaUrl: string;
    mediaType: 'audio' | 'video';
    originalFilename?: string;
    className?: string;
    sessionId?: string;
    onUrlRefresh?: (newUrl: string) => void;
}

export default function MediaPlayer({ 
    mediaUrl, 
    mediaType, 
    originalFilename,
    className = "",
    sessionId,
    onUrlRefresh
}: MediaPlayerProps) {
    const [currentUrl, setCurrentUrl] = useState(mediaUrl);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleDownload = () => {
        // Create a temporary link to download the file
        const link = document.createElement('a');
        link.href = currentUrl;
        link.download = originalFilename || 'download';
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const handleMediaError = async () => {
        console.error('Media failed to load, possibly due to expired signed URL');
        setError('Media failed to load. The link may have expired.');
        
        // If we have a session ID, try to refresh the URL
        if (sessionId && onUrlRefresh) {
            await refreshUrl();
        }
    };

    const refreshUrl = async () => {
        if (!sessionId) return;

        setIsRefreshing(true);
        setError(null);

        try {
            const { sessionApi } = await import('../lib/api');
            
            // First try to refresh the URL
            let response;
            try {
                response = await sessionApi.refreshMediaUrl(sessionId);
            } catch (refreshError: any) {
                // If refresh fails due to missing blob name, try to fix it first
                if (refreshError.response?.data?.error?.includes('No GCS blob name found')) {
                    console.log('🔧 Attempting to fix missing blob name...');
                    await sessionApi.fixBlobName(sessionId);
                    // Now retry the refresh
                    response = await sessionApi.refreshMediaUrl(sessionId);
                } else {
                    throw refreshError;
                }
            }
            
            const newUrl = response.media_url;
            
            setCurrentUrl(newUrl);
            if (onUrlRefresh) {
                onUrlRefresh(newUrl);
            }
        } catch (err: any) {
            console.error('Failed to refresh media URL:', err);
            const errorMessage = err.response?.data?.error || 'Failed to refresh the media link. Please try again later.';
            setError(errorMessage);
        } finally {
            setIsRefreshing(false);
        }
    };

    if (mediaType === 'video') {
        return (
            <div className={`space-y-4 ${className}`}>
                {error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-red-700 text-sm font-medium">Media Loading Error</p>
                                <p className="text-red-600 text-xs mt-1">{error}</p>
                            </div>
                            {sessionId && (
                                <button
                                    onClick={refreshUrl}
                                    disabled={isRefreshing}
                                    className="bg-red-100 hover:bg-red-200 text-red-700 px-3 py-1 rounded text-sm font-medium disabled:opacity-50 whitespace-nowrap ml-3"
                                >
                                    {isRefreshing ? 'Fixing...' : 'Fix & Refresh'}
                                </button>
                            )}
                        </div>
                    </div>
                )}
                
                <video
                    controls
                    className="w-full max-h-96 rounded-lg"
                    src={currentUrl}
                    preload="metadata"
                    style={{ backgroundColor: '#f3f4f6' }}
                    onError={handleMediaError}
                >
                    Your browser does not support the video tag.
                </video>
                <div className="flex items-center justify-between text-sm text-gray-600">
                    {originalFilename && (
                        <span>Original file: {originalFilename}</span>
                    )}
                    <button
                        onClick={handleDownload}
                        className="text-blue-600 hover:text-blue-800 hover:underline font-medium"
                    >
                        📥 Download Video
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className={`space-y-4 ${className}`}>
            {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
                    <div className="flex items-center justify-between">
                        <p className="text-red-700 text-sm">{error}</p>
                        {sessionId && (
                            <button
                                onClick={refreshUrl}
                                disabled={isRefreshing}
                                className="bg-red-100 hover:bg-red-200 text-red-700 px-3 py-1 rounded text-sm font-medium disabled:opacity-50"
                            >
                                {isRefreshing ? 'Refreshing...' : 'Refresh Link'}
                            </button>
                        )}
                    </div>
                </div>
            )}
            
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border-2 border-blue-200">
                <div className="flex items-center space-x-3 mb-3">
                    <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center">
                        🎵
                    </div>
                    <div>
                        <h3 className="font-medium text-gray-900">Audio Recording</h3>
                        {originalFilename && (
                            <p className="text-sm text-gray-600">{originalFilename}</p>
                        )}
                    </div>
                </div>
                
                <audio
                    controls
                    className="w-full"
                    src={currentUrl}
                    preload="metadata"
                    onError={handleMediaError}
                    style={{ 
                        filter: 'sepia(0) hue-rotate(200deg) saturate(1.2)',
                        borderRadius: '8px'
                    }}
                >
                    Your browser does not support the audio tag.
                </audio>
                
                <div className="flex items-center justify-between mt-3">
                    <div className="text-xs text-gray-500">
                        💡 Use the controls above to play, pause, and adjust volume
                    </div>
                    <button
                        onClick={handleDownload}
                        className="text-blue-600 hover:text-blue-800 hover:underline font-medium text-sm"
                    >
                        📥 Download Audio
                    </button>
                </div>
            </div>
            
            {/* Fallback link if audio doesn't work */}
            <div className="text-center">
                <p className="text-sm text-gray-500 mb-2">
                    Can&apos;t play the audio? 
                </p>
                <div className="space-x-4">
                    <a 
                        href={currentUrl} 
                        className="text-blue-600 hover:underline font-medium"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        Open in new tab
                    </a>
                    {sessionId && (
                        <button
                            onClick={refreshUrl}
                            disabled={isRefreshing}
                            className="text-orange-600 hover:underline font-medium disabled:opacity-50"
                        >
                            {isRefreshing ? 'Fixing...' : 'Fix & Refresh'}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}