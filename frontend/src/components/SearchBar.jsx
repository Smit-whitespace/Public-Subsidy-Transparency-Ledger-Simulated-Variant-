import React from "react";

export default function SearchBar({
  value = "",
  placeholder = "Search...",
  onChange = () => {},
  onSubmit = () => {}
}) {
  function handleKeyDown(e) {
    if (e.key === "Enter") {
      e.preventDefault();
      onSubmit(value);
    }
  }

  function handleButtonClick() {
    onSubmit(value);
  }

  function handleInputChange(e) {
    onChange(e.target.value);
  }

  return (
    <div className="search-bar">
      <input
        type="search"
        value={value}
        placeholder={placeholder}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
      />
      <button type="button" onClick={handleButtonClick}>
        Search
      </button>
    </div>
  );
}