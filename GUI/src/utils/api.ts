// Simple API utility function
export const apiCall = async (
  endpoint: string,
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' = 'GET',
  body?: any
): Promise<[boolean, any]> => {
  try {
    const options: RequestInit = {
      method,
      headers: { 'Content-Type': 'application/json' },
    };

    if (body && method !== 'GET') {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(endpoint, options);

    if (!response.ok) {
      // read error body once
      const errText = await response.text();
      console.error(`[${method} ${endpoint}] failed ${response.status}:`, errText);
      return [false, errText];
    }

    // only parse if success
    const contentType = response.headers.get('content-type');
    let data;
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    return [true, data];
  } catch (error) {
    console.error(`API call error [${method} ${endpoint}]:`, error);
    return [false, error];
  }
};




// // GET request example
// const [ok1, data1] = await apiCall('/api/users');
// console.log(ok1, data1);

// // POST request example
// const [ok2, data2] = await apiCall('/api/users', 'POST', { name: 'Alice' });
// console.log(ok2, data2);
