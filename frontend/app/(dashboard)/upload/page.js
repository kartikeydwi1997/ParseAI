import UploadForm from '@/components/UploadForm';

const UploadPage = () => {
  return (
    <div className='max-w-2xl mx-auto'>
      <h1 className='text-4xl font-bold mb-8 text-center'>Upload Project</h1>
      <UploadForm />
    </div>
  );
};

export default UploadPage;