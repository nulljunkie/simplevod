package utils

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestSanitizeLabel_ValidInput(t *testing.T) {
	input := "valid-label-123"
	expected := "valid-label-123"

	result := SanitizeLabel(input)

	assert.Equal(t, expected, result)
}

func TestSanitizeLabel_InvalidCharacters(t *testing.T) {
	input := "invalid@label#with$special%chars"
	expected := "invalid-label-with-special-chars"

	result := SanitizeLabel(input)

	assert.Equal(t, expected, result)
}

func TestSanitizeLabel_TooLong(t *testing.T) {
	input := "this-is-a-very-long-label-name-that-exceeds-the-kubernetes-limit-of-63-characters-and-should-be-truncated"

	result := SanitizeLabel(input)

	assert.LessOrEqual(t, len(result), 63)
	assert.True(t, len(result) > 0)
}

func TestSanitizeLabel_StartsWithSpecialChar(t *testing.T) {
	input := "-starts-with-dash"

	result := SanitizeLabel(input)

	assert.Equal(t, "starts-with-dash", result)
}

func TestSanitizeLabel_EndsWithSpecialChar(t *testing.T) {
	input := "ends-with-dash-"

	result := SanitizeLabel(input)

	assert.Equal(t, "ends-with-dash", result)
}

func TestSanitizeLabel_EmptyInput(t *testing.T) {
	input := ""
	expected := "default-label"

	result := SanitizeLabel(input)

	assert.Equal(t, expected, result)
}

func TestSanitizeLabel_OnlySpecialChars(t *testing.T) {
	input := "@#$%^&*()"
	expected := "default-label"

	result := SanitizeLabel(input)

	assert.Equal(t, expected, result)
}

func TestSanitizeLabel_MixedCase(t *testing.T) {
	input := "MixedCaseLabel"
	expected := "mixedcaselabel"

	result := SanitizeLabel(input)

	assert.Equal(t, expected, result)
}

func TestSanitizeLabel_WithSpaces(t *testing.T) {
	input := "label with spaces"
	expected := "label-with-spaces"

	result := SanitizeLabel(input)

	assert.Equal(t, expected, result)
}

func TestSanitizeLabel_UnicodeCharacters(t *testing.T) {
	input := "label-with-unicode-ñ-chars"
	expected := "label-with-unicode---chars"

	result := SanitizeLabel(input)

	assert.Equal(t, expected, result)
}

func TestSanitizeLabel_PreservesValidChars(t *testing.T) {
	input := "abc123-XYZ.test_label"
	expected := "abc123-xyz.test_label"

	result := SanitizeLabel(input)

	assert.Equal(t, expected, result)
}

func TestSanitizeLabel_EdgeCases(t *testing.T) {
	testCases := []struct {
		input    string
		expected string
	}{
		{"a", "a"},
		{"1", "1"},
		{"-", "default-label"},
		{"a-", "a"},
		{"-a", "a"},
		{"a-b", "a-b"},
	}

	for _, tc := range testCases {
		result := SanitizeLabel(tc.input)
		assert.Equal(t, tc.expected, result, "Failed for input: %s", tc.input)
	}
}

func TestSanitizeLabel_KubernetesCompliance(t *testing.T) {
	testCases := []string{
		"video-id-12345",
		"transcode-job-240p",
		"config-map-name",
		"very-long-video-id-that-might-exceed-limits-in-kubernetes",
	}

	for _, input := range testCases {
		result := SanitizeLabel(input)

		assert.LessOrEqual(t, len(result), 63, "Label too long: %s", result)
		assert.Regexp(t, "^[a-z0-9]([a-z0-9-]*[a-z0-9])?$", result, "Invalid label format: %s", result)
	}
}

