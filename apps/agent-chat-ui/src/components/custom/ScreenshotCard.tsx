"use client";

import React, { useState } from "react";
import Image from "next/image";
import { Maximize2, X as XIcon, Clock, Scan } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * ScreenshotCard - Displays analyzed screenshots with OCR results
 *
 * Receives screenshot data from backend with OCR extracted text, translations,
 * and metadata. Supports click-to-expand for full-size viewing.
 */

interface ExtractedTextSegment {
  text: string;
  reading?: string;
  confidence: number;
}

interface ScreenshotCardProps {
  image_data: string;      // base64 encoded
  media_type: string;      // e.g., "image/png"
  extracted_text: ExtractedTextSegment[];
  translation?: string;
  ocr_method: "claude" | "manga-ocr" | "hybrid";
  processed_at: string;    // ISO 8601 timestamp
}

export default function ScreenshotCard({
  image_data,
  media_type,
  extracted_text,
  translation,
  ocr_method,
  processed_at,
}: ScreenshotCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  // Construct data URL for base64 image
  const imageUrl = `data:${media_type};base64,${image_data}`;

  // Format timestamp for display
  const formattedTime = new Date(processed_at).toLocaleString();

  // Get OCR method display name
  const ocrMethodLabel = {
    claude: "Claude Vision",
    "manga-ocr": "Manga OCR",
    hybrid: "Hybrid (Manga OCR + Claude)",
  }[ocr_method];

  return (
    <>
      {/* Main Card */}
      <div className="rounded-xl border-2 border-purple-500 bg-purple-50 p-6 shadow-md max-w-2xl my-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-purple-900">
            Screenshot Analysis
          </h3>
          <button
            onClick={() => setIsExpanded(true)}
            className="p-2 rounded-lg hover:bg-purple-100 transition-colors"
            aria-label="Expand image"
          >
            <Maximize2 className="h-5 w-5 text-purple-700" />
          </button>
        </div>

        {/* Image Container */}
        <div className="relative bg-white rounded-lg overflow-hidden mb-4" style={{ maxWidth: "600px" }}>
          {!imageLoaded && !imageError && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
              <div className="flex gap-1">
                <div className="h-2 w-2 bg-purple-500 rounded-full animate-[pulse_1.5s_ease-in-out_infinite]" />
                <div className="h-2 w-2 bg-purple-500 rounded-full animate-[pulse_1.5s_ease-in-out_0.5s_infinite]" />
                <div className="h-2 w-2 bg-purple-500 rounded-full animate-[pulse_1.5s_ease-in-out_1s_infinite]" />
              </div>
            </div>
          )}

          {imageError ? (
            <div className="flex items-center justify-center p-8 bg-red-50">
              <p className="text-red-600 text-sm">Failed to load image</p>
            </div>
          ) : (
            <Image
              src={imageUrl}
              alt="Screenshot with Japanese text"
              width={600}
              height={400}
              className="w-full h-auto object-contain cursor-pointer"
              style={{ maxHeight: "400px" }}
              onLoad={() => setImageLoaded(true)}
              onError={() => setImageError(true)}
              onClick={() => setIsExpanded(true)}
              unoptimized // Required for base64 data URLs
            />
          )}
        </div>

        {/* Extracted Text Section */}
        {extracted_text && extracted_text.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-semibold text-purple-900 mb-2">
              Extracted Text:
            </h4>
            <div className="bg-white rounded-lg p-3 space-y-2">
              {extracted_text.map((segment, idx) => (
                <div key={idx} className="flex flex-col">
                  <div className="flex items-baseline gap-2">
                    <span className="text-base text-gray-900 font-medium">
                      {segment.text}
                    </span>
                    {segment.reading && (
                      <span className="text-sm text-gray-500 italic">
                        ({segment.reading})
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-gray-400">
                    Confidence: {Math.round(segment.confidence * 100)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Translation Section */}
        {translation && (
          <div className="mb-4">
            <h4 className="text-sm font-semibold text-purple-900 mb-2">
              Translation:
            </h4>
            <div className="bg-white rounded-lg p-3">
              <p className="text-gray-700 text-sm">{translation}</p>
            </div>
          </div>
        )}

        {/* Metadata Footer */}
        <div className="flex items-center gap-4 text-xs text-gray-500 pt-3 border-t border-purple-200">
          <div className="flex items-center gap-1">
            <Scan className="h-4 w-4" />
            <span>{ocrMethodLabel}</span>
          </div>
          <div className="flex items-center gap-1">
            <Clock className="h-4 w-4" />
            <span>{formattedTime}</span>
          </div>
        </div>
      </div>

      {/* Expanded View Modal */}
      {isExpanded && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-80 p-4"
          onClick={() => setIsExpanded(false)}
        >
          <div className="relative max-w-5xl max-h-[90vh]">
            <button
              onClick={() => setIsExpanded(false)}
              className="absolute -top-10 right-0 p-2 rounded-full bg-white text-gray-800 hover:bg-gray-200 transition-colors"
              aria-label="Close expanded view"
            >
              <XIcon className="h-6 w-6" />
            </button>
            <Image
              src={imageUrl}
              alt="Screenshot with Japanese text (expanded)"
              width={1200}
              height={800}
              className="rounded-lg object-contain max-h-[90vh]"
              unoptimized
            />
          </div>
        </div>
      )}
    </>
  );
}
