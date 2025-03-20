'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { uploadProject } from '@/utils/actions';
const UploadForm = () => {
  const [file, setFile] = useState(null);
  const allowedFileTypes = [
    'application/zip',
    'application/x-tar',
    'application/gzip',
    'application/x-gzip'
  ];

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    
    if (!selectedFile) return;

    if (!allowedFileTypes.includes(selectedFile.type)) {
      toast.error('Please upload only .zip, .tar, .tgz, or .tar.gz files');
      e.target.value = ''; // Reset input
      return;
    }

    setFile(selectedFile);
  };

  const { mutate, isPending } = useMutation({
    mutationFn: async (formData) => {
      // FastAPI expects files array
      const result = await uploadProject(formData);
      if (!result.success) {
        throw new Error(result.error);
      }
      return result.data;
    },
    onSuccess: (data) => {
      console.log('Project uploaded:', data); 
      toast.success('Project uploaded successfully');
      setFile(null);
      // Reset the file input
      const fileInput = document.querySelector('input[type="file"]');
      if (fileInput) fileInput.value = '';
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to upload project');
    },
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file) {
      toast.error('Please select a file');
      return;
    }
  
    // Check file size (2MB limit)
    if (file.size > 2 * 1024 * 1024) {
      toast.error('File size exceeds 2MB limit');
      return;
    }
  
    const formData = new FormData();
    // FastAPI expects 'files' as the field name
    formData.append('file', file);
    
    mutate(formData);
  };

  return (
    <form onSubmit={handleSubmit} className='space-y-4'>
      <fieldset className='fieldset border rounded-lg p-4'>
        <legend className='fieldset-legend font-semibold px-2'>Select the Project</legend>
        <input
          type='file'
          className='file-input w-full'
          onChange={handleFileChange}
          accept='.zip,.tar,.tgz,.tar.gz'
        />
  <label className='fieldset-label text-sm text-gray-500'>
          Accepted formats: .zip, .tar, .tgz, .tar.gz (Max size 2MB)
        </label>
      </fieldset>
      <button
        type='submit'
        className='btn btn-primary w-full'
        disabled={isPending}
      >
        {isPending ? 'Uploading...' : 'Upload Project'}
      </button>
    </form>
  );
};

export default UploadForm;