'use server';
import OpenAI from 'openai';
import prisma from './db';
import { revalidatePath } from 'next/cache';
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});
console.log('API KEY:', process.env.OPENAI_API_KEY);
export const generateChatResponse = async (chatMessages) => {
  try {
    const response = await openai.chat.completions.create({
      messages: [
        { role: 'system', content: 'you are a helpful assistant' },
        ...chatMessages,
      ],
      model: 'gpt-3.5-turbo',
      temperature: 0,
      max_tokens: 100,
    });
    return {
      message: response.choices[0].message,
      tokens: response.usage.total_tokens,
    };
  } catch (error) {
    console.log(error);
    return null;
  }
};

export const generateTourResponse = async ({ city, country }) => {
  const query = `Find a exact ${city} in this exact ${country}.
If ${city} and ${country} exist, create a list of things families can do in this ${city},${country}. 
Once you have a list, create a one-day tour. Response should be  in the following JSON format: 
{
  "tour": {
    "city": "${city}",
    "country": "${country}",
    "title": "title of the tour",
    "description": "short description of the city and tour",
    "stops": [" stop name", "stop name","stop name"]
  }
}
"stops" property should include only three stops.
If you can't find info on exact ${city}, or ${city} does not exist, or it's population is less than 1, or it is not located in the following ${country},   return { "tour": null }, with no additional characters.`;
  try {
    const response = await openai.chat.completions.create({
      messages: [
        { role: 'system', content: 'you are a tour guide' },
        {
          role: 'user',
          content: query,
        },
      ],
      model: 'gpt-3.5-turbo',
      temperature: 0,
    });

    const tourData = JSON.parse(response.choices[0].message.content);
    if (!tourData.tour) {
      return null;
    }
    return { tour: tourData.tour, tokens: response.usage.total_tokens };
  } catch (error) {
    console.log(error);
    return null;
  }
};

export const getExistingTour = async ({ city, country }) => {
  return prisma.tour.findUnique({
    where: {
      city_country: {
        city,
        country,
      },
    },
  });
};

export const createNewTour = async (tour) => {
  return prisma.tour.create({
    data: tour,
  });
};

export const getAllTours = async (searchTerm) => {
  if (!searchTerm) {
    const tours = await prisma.tour.findMany({
      orderBy: {
        city: 'asc',
      },
    });
    return tours;
  }
  const tours = await prisma.tour.findMany({
    where: {
      OR: [
        {
          city: {
            contains: searchTerm,
          },
        },
        {
          country: {
            contains: searchTerm,
          },
        },
      ],
    },
    orderBy: {
      city: 'asc',
    },
  });

  return tours;
};

export const getSingleTour = async (id) => {
  return prisma.tour.findUnique({
    where: {
      id,
    },
  });
};

export const generateTourImage = async ({ city, country }) => {
  try {
    const tourImage = await openai.images.generate({
      prompt: `a panoramic view of teh ${city} ${country}`,
      n: 1,
      size: '512x512',
    });
    return tourImage?.data[0]?.url;
  } catch (error) {
    return null;
  }
};

export const fetchUserTokensById = async (clerkId) => {
  // const result = await prisma.token.findUnique({
  //   where: {
  //     clerkId,
  //   },
  // });
return 1000;
  //return result?.tokens;
};

export const generateUserTokensForId = async (clerkId) => {
  // const result = await prisma.token.create({
  //   data: {
  //     clerkId,
  //   },
  // });
  // return result?.tokens;
  return 1000;
};

export const fetchOrGenerateTokens = async (clerkId) => {
  // const result = await fetchUserTokensById(clerkId);
  // if (result) {
  //   return result.tokens;
  // }
  // return (await generateUserTokensForId(clerkId)).tokens;
  return 1000;
};

export const subtractTokens = async (clerkId, tokens) => {
  const result = await prisma.token.update({
    where: {
      clerkId,
    },
    data: {
      tokens: {
        decrement: tokens,
      },
    },
  });
  revalidatePath('/profile');
  // Return the new token value
  return result.tokens;
};

export const uploadProject = async (formData) => {
  console.log('Uploading project...');
  console.log('Form data:', formData);
  try {
    const response = await fetch('http://localhost:8000/upload/', {
      method: 'POST',
      body: formData,
      headers: {
        'Accept': 'application/json',
      },
    });
    
    const data = await response.json();
    console.log('Upload response:', data);
    if (!response.ok) {
      throw new Error(data.detail || 'Upload failed');
    }
    
   
    return { 
      success: true, 
      data: {
        projectId: data.projectId
      }
    };
  } catch (error) {
    console.error('Upload error:', error);
    return { 
      success: false, 
      error: error.message || 'Failed to upload project'
    };
  }
};

export const queryProject = async (projectId, messages) => {
  console.log('Querying project:', projectId);
  console.log('Messages:', messages);
  
  try {
    const response = await fetch('http://localhost:8001/query/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        project_id: projectId,
        messages: messages
      }),
    });
    
    const data = await response.json();
    console.log('Query response:', data);
    
    if (!response.ok) {
      throw new Error(data.detail || 'Query failed');
    }
    
    return { 
      success: true, 
      data: data
    };
  } catch (error) {
    console.error('Query error:', error);
    return { 
      success: false, 
      error: error.message || 'Failed to process query'
    };
  }
};