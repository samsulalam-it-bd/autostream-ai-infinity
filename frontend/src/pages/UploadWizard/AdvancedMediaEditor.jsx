import React, { useRef } from 'react';
import { Rnd } from 'react-rnd';
import { useWizard } from './WizardContext';
import { Trash2 } from 'lucide-react';

export default function AdvancedMediaEditor({ videoSrc, selectedVideoId }) {
    const { state, dispatch } = useWizard();
    const parentRef = useRef(null);

    // Filter elements to only this specific video if we ever support multi-video editing at once
    // For now, editing applies globally or to the currently active video in view.
    const activeElements = state.editorElements; // Alternatively: .filter(el => el.videoId === selectedVideoId)

    // QA Logic: Prevent elements from dragging outside the video bounds
    const onDragStop = (id, d) => {
        dispatch({ type: 'UPDATE_EDITOR_ELEMENT', payload: { id, x: d.x, y: d.y } });
    };

    const onResizeStop = (id, ref, position) => {
        dispatch({
            type: 'UPDATE_EDITOR_ELEMENT',
            payload: { id, width: ref.style.width, height: ref.style.height, ...position }
        });
    };

    const removeElement = (id) => {
        dispatch({ type: 'REMOVE_EDITOR_ELEMENT', payload: id });
    };

    return (
        <div className="relative w-full max-w-3xl max-h-[60vh] aspect-auto bg-black/50 rounded-lg overflow-hidden border border-white/10 shadow-xl flex justify-center" ref={parentRef}>
            {/* Base Video */}
            {videoSrc ? (
                <video src={videoSrc} className="w-auto h-full max-h-[60vh] object-contain pointer-events-none" autoPlay loop muted />
            ) : (
                <div className="w-full h-48 flex items-center justify-center text-white/30">
                    No video selected for preview
                </div>
            )}

            {/* Interactive Overlays */}
            {activeElements.map((el) => (
                <Rnd
                    key={el.id}
                    bounds="parent" // strictly inside the video frame
                    size={{ width: el.width, height: el.height }}
                    position={{ x: el.x, y: el.y }}
                    onDragStop={(e, d) => onDragStop(el.id, d)}
                    onResizeStop={(e, direction, ref, delta, position) => onResizeStop(el.id, ref, position)}
                    className={`absolute group ${el.type === 'text' ? 'text-white font-bold text-2xl' : ''}`}
                >
                    {/* Delete Button (visible on hover) */}
                    <button
                        onClick={() => removeElement(el.id)}
                        className="absolute -top-3 -right-3 z-50 bg-red-500 rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Remove Element"
                    >
                        <Trash2 className="w-3 h-3 text-white" />
                    </button>

                    {el.type === 'text' ? (
                        <div className="w-full h-full flex items-center justify-center p-2 border-2 border-dashed border-transparent hover:border-brand-500 cursor-move"
                            style={{ color: el.color || 'white', backgroundColor: el.bgColor || 'transparent' }}>
                            {el.content}
                        </div>
                    ) : (
                        <div className="w-full h-full border-2 border-dashed border-transparent hover:border-brand-500 cursor-move">
                            <img src={el.content} className="w-full h-full object-contain pointer-events-none" alt="Overlay Logo" />
                        </div>
                    )}
                </Rnd>
            ))}
        </div>
    );
}
