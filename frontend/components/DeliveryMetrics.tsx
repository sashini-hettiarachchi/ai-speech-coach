import React from "react";

export type DeliveryMetrics = {
  duration: number;
  mean_intensity: number;
  mean_pitch: number;
  pitch_variation: number;
  word_count: number;
  wpm: number;
};

interface DeliveryMetricsProps {
  metrics: DeliveryMetrics;
}

const DeliveryMetricsTable: React.FC<DeliveryMetricsProps> = ({ metrics }) => {
  return (
    <div className="w-full bg-white rounded-md shadow-sm p-4 mb-4">
      <h3 className="text-lg font-semibold mb-2">Delivery Metrics</h3>
      <table className="min-w-full text-left border border-gray-200 rounded-md">
        <tbody>
          <tr>
            <td className="py-2 px-4 font-medium">Duration (s)</td>
            <td className="py-2 px-4">{metrics.duration}</td>
          </tr>
          <tr>
            <td className="py-2 px-4 font-medium">Mean Intensity</td>
            <td className="py-2 px-4">{metrics.mean_intensity}</td>
          </tr>
          <tr>
            <td className="py-2 px-4 font-medium">Mean Pitch (Hz)</td>
            <td className="py-2 px-4">{metrics.mean_pitch}</td>
          </tr>
          <tr>
            <td className="py-2 px-4 font-medium">Pitch Variation</td>
            <td className="py-2 px-4">{metrics.pitch_variation}</td>
          </tr>
          <tr>
            <td className="py-2 px-4 font-medium">Word Count</td>
            <td className="py-2 px-4">{metrics.word_count}</td>
          </tr>
          <tr>
            <td className="py-2 px-4 font-medium">Words Per Minute (WPM)</td>
            <td className="py-2 px-4">{metrics.wpm}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
};

export default DeliveryMetricsTable;
