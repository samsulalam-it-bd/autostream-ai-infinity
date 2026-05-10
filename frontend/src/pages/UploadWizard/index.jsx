import React from 'react';
import { WizardProvider, useWizard } from './WizardContext';
import Step1Accounts from './Step1Accounts';
import Step2DriveLink from './Step2DriveLink';
import Step3MetadataEditor from './Step3MetadataEditor';
import Step4Schedule from './Step4Schedule';
import Step5Review from './Step5Review';
import { Check } from 'lucide-react';

const steps = [
    { id: 1, title: 'Targets' },
    { id: 2, title: 'Media' },
    { id: 3, title: 'Editor' },
    { id: 4, title: 'Schedule' },
    { id: 5, title: 'Review' }
];

function WizardContent() {
    const { state } = useWizard();

    return (
        <div className="max-w-7xl mx-auto space-y-8">
            {/* Stepper UI */}
            <div className="relative mb-12">
                <div className="absolute top-1/2 left-0 w-full h-0.5 bg-white/10 -translate-y-1/2 z-0 hidden sm:block"></div>
                <div className="absolute top-1/2 left-0 h-0.5 bg-brand-500 -translate-y-1/2 z-0 hidden sm:block transition-all duration-500"
                    style={{ width: `${((state.currentStep - 1) / (steps.length - 1)) * 100}%` }}></div>

                <div className="relative z-10 flex justify-between">
                    {steps.map((step) => {
                        const isCompleted = state.currentStep > step.id;
                        const isCurrent = state.currentStep === step.id;

                        return (
                            <div key={step.id} className="flex flex-col items-center gap-2">
                                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all duration-300
                  ${isCompleted ? 'bg-brand-500 text-white shadow-[0_0_15px_rgba(99,102,241,0.5)]' :
                                        isCurrent ? 'bg-brand-600 border-2 border-white text-white shadow-[0_0_20px_rgba(99,102,241,0.6)]' :
                                            'bg-slate-800 border-2 border-white/20 text-white/40'}`}
                                >
                                    {isCompleted ? <Check className="w-5 h-5" /> : step.id}
                                </div>
                                <span className={`text-xs font-semibold tracking-wide uppercase hidden sm:block transition-colors
                  ${isCurrent ? 'text-brand-300' : isCompleted ? 'text-white/80' : 'text-white/30'}`}>
                                    {step.title}
                                </span>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Render Current Step */}
            <div className="bg-slate-900/50 rounded-2xl p-6 sm:p-8 border border-white/5 shadow-2xl backdrop-blur-xl">
                {state.currentStep === 1 && <Step1Accounts />}
                {state.currentStep === 2 && <Step2DriveLink />}
                {state.currentStep === 3 && <Step3MetadataEditor />}
                {state.currentStep === 4 && <Step4Schedule />}
                {state.currentStep === 5 && <Step5Review />}
            </div>
        </div>
    );
}

export default function UploadWizard() {
    return (
        <WizardProvider>
            <WizardContent />
        </WizardProvider>
    );
}
