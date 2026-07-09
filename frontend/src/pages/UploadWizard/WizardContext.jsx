import React, { createContext, useReducer, useContext } from 'react';

const initialState = {
    currentStep: 1,

    // Step 1
    selectedAccounts: [],
    groupName: "",

    // Step 2
    driveLink: "",
    fetchedMedia: [],
    selectedMedia: [], // videos they actively pick to move to step 3

    // Step 3
    metadataConfig: {
        mode: "manual",
        customTitle: "",
        customDescription: "",
        tags: "",
        addWatermark: false,
        video_editing: true
    },
    editorElements: [], // { id, type: 'logo'|'text', x, y, width, height, content }

    // Step 4
    scheduleConfig: {
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        slots: [], // [{time: '09:00', ...}]
        commentMode: "none", // none, auto, manual, auto_manual
        manualComment: "",
        frequency: 1,
        selectedDates: [] // optional specific calendar dates
    }
};

function wizardReducer(state, action) {
    switch (action.type) {
        case 'GO_TO_STEP':
            return { ...state, currentStep: action.payload };
        case 'SET_ACCOUNTS':
            return { ...state, selectedAccounts: action.payload };
        case 'SET_GROUP_NAME':
            return { ...state, groupName: action.payload };
        case 'UPDATE_DRIVE_DATA':
            return { ...state, driveLink: action.payload.link, fetchedMedia: action.payload.media };
        case 'SET_SELECTED_MEDIA':
            return { ...state, selectedMedia: action.payload };
        case 'SET_METADATA_CONFIG':
            return { ...state, metadataConfig: { ...state.metadataConfig, ...action.payload } };
        case 'ADD_EDITOR_ELEMENT':
            return { ...state, editorElements: [...state.editorElements, action.payload] };
        case 'REMOVE_EDITOR_ELEMENT':
            return { ...state, editorElements: state.editorElements.filter(el => el.id !== action.payload) };
        case 'UPDATE_EDITOR_ELEMENT':
            return {
                ...state,
                editorElements: state.editorElements.map(el => el.id === action.payload.id ? { ...el, ...action.payload } : el)
            };
        case 'SET_SCHEDULE':
            return { ...state, scheduleConfig: { ...state.scheduleConfig, ...action.payload } };
        case 'RESET_WIZARD':
            return initialState;
        default:
            return state;
    }
}

export const WizardContext = createContext();

export const WizardProvider = ({ children }) => {
    const [state, dispatch] = useReducer(wizardReducer, initialState);
    return (
        <WizardContext.Provider value={{ state, dispatch }}>
            {children}
        </WizardContext.Provider>
    );
};

export const useWizard = () => useContext(WizardContext);
