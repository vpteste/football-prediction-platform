import React, { useState } from 'react';
import './Autocomplete.css';

interface AutocompleteProps {
    suggestions: string[];
    onSelect: (value: string) => void;
    value: string;
    onChange: (value: string) => void;
}

const Autocomplete: React.FC<AutocompleteProps> = ({ suggestions, onSelect, value, onChange }) => {
    const [filteredSuggestions, setFilteredSuggestions] = useState<string[]>([]);
    const [showSuggestions, setShowSuggestions] = useState<boolean>(false);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const userInput = e.currentTarget.value;
        const filtered = suggestions.filter(
            suggestion =>
                suggestion.toLowerCase().indexOf(userInput.toLowerCase()) > -1 &&
                suggestion.toLowerCase() !== userInput.toLowerCase()
        );

        onChange(userInput);
        setFilteredSuggestions(filtered);
        setShowSuggestions(true);
    };

    const handleSelect = (suggestion: string) => {
        onSelect(suggestion);
        setShowSuggestions(false);
    };

    const suggestionsListComponent = () => {
        if (showSuggestions && value) {
            if (filteredSuggestions.length) {
                return (
                    <ul className="suggestions" onMouseDown={(e) => e.preventDefault()}>
                        {filteredSuggestions.map((suggestion, index) => {
                            return (
                                <li key={suggestion} onClick={() => handleSelect(suggestion)}>
                                    {suggestion}
                                </li>
                            );
                        })}
                    </ul>
                );
            }
        }
        return null;
    };

    return (
        <div className="autocomplete-wrapper">
            <input
                type="text"
                onChange={handleChange}
                value={value}
                onBlur={() => setShowSuggestions(false)}
            />
            {suggestionsListComponent()}
        </div>
    );
};

export default Autocomplete;