import numpy as np
import math
from numba import cuda,float64,int64
import time
import Layers

    
@cuda.jit("float64[:,:,:,:],float64[:,:,:],float64[:,:,:,:],float64[:,:,:],int64,int64,int64,int64")
def conv_step_forward3D(W,img,b,Z,stride,xlim,ylim,zlim):

    """
    W -- (fH,fW,n_C_prev,n_C)
    img -- (n_H_prev,n_W_prev,n_C_prev)
    b -- (1,1,1,n_C)
    Z -- (n_H,n_W,n_C)
    """

    fH,fW,n_C_prev,n_C = W.shape
    n_H_prev,n_W_prev,n_C_prev = img.shape
    
    n_H = cuda.threadIdx.x + cuda.blockIdx.x*cuda.blockDim.x
    n_W = cuda.threadIdx.y + cuda.blockIdx.y*cuda.blockDim.y
    n_C = cuda.threadIdx.z + cuda.blockIdx.z*cuda.blockDim.z

    if (n_H < xlim) and (n_W < ylim) and (n_C < zlim):

        #loop through height
        for h in range(fH):

            #loop through width
            for w in range(fW):

                #loop through channels
                for c in range(n_C_prev):

                    IMG_H = n_H*stride+h
                    IMG_W = n_W*stride+w

                    Z[n_H,n_W,n_C] = Z[n_H,n_W,n_C] + W[h,w,c,n_C]*img[IMG_H,IMG_W,c]

        #wait until result come out
        cuda.syncthreads()

        #add bias
        Z[n_H,n_W,n_C] = Z[n_H,n_W,n_C] + float(b[0,0,0,n_C])

        #wait until result come out
        cuda.syncthreads()


@cuda.jit("float64[:,:,:],float64[:,:],float64[:,:,:],float64[:,:,:],int64,int64,int64,int64")
def conv_step_forward3D(W,img,b,Z,stride,xlim,ylim,zlim):

    """
    W -- (fH,fW,n_C)
    img -- (n_H_prev,n_W_prev)
    b -- (1,1,n_C)
    Z -- (n_H,n_W,n_C)
    """

    fH,fW,n_C = W.shape
    n_H_prev,n_W_prev = img.shape
    
    n_H = cuda.threadIdx.x + cuda.blockIdx.x * cuda.blockDim.x
    n_W = cuda.threadIdx.y + cuda.blockIdx.y * cuda.blockDim.y
    n_C = cuda.threadIdx.z + cuda.blockIdx.z * cuda.blockDim.z

    if (n_H < xlim) and (n_W < ylim) and (n_C < zlim):

        #loop through height
        for h in range(fH):

            #loop through width
            for w in range(fW):

                IMG_H = n_H * stride + h
                IMG_W = n_W * stride + w
                
                Z[n_H,n_W,n_C] = Z[n_H,n_W,n_C] + W[h,w,n_C]*img[IMG_H,IMG_W]

        #wait result
        cuda.syncthreads()

        #Add Bias
        Z[n_H,n_W,n_C] = Z[n_H,n_W,n_C] + float(b[0,0,n_C])

        #wait result
        cuda.syncthreads()


if __name__ == "__main__":

    """
    #3D
    #GPU
    W = np.random.randn(3,3,3,16)
    b = np.random.randn(1,1,1,16)
    Img = np.random.randn(1,1080,1920,3)

    m,n_H_prev,n_W_prev,n_C_prev = Img.shape

    fH,fW = W.shape[0],W.shape[1]
    
    stride = 2
    n_H = int((n_H_prev-fH)/stride)+1
    n_W = int((n_W_prev-fW)/stride)+1
    n_C = 16
    
    Z = np.zeros((n_H,n_W,16))
    
    threadsperblock = (8,8,2)

    blockspergrid_H = int(math.ceil(Z.shape[0]/threadsperblock[0]))
    blockspergrid_W = int(math.ceil(Z.shape[1]/threadsperblock[1]))
    blockspergrid_C = int(math.ceil(Z.shape[2]/threadsperblock[2]))

    blockspergrid = (blockspergrid_H,blockspergrid_W,blockspergrid_C)

    
    W_device = cuda.to_device(W)
    Img_device = cuda.to_device(Img[0,:,:,:])
    Z_device = cuda.to_device(Z)
    b_device = cuda.to_device(b)
    
    """
    #W_device = cuda.device_array_like(W)
    #Img_device = cuda.device_array_like(Img[0,:,:,:])
    #Z_device = cuda.device_array_like(Z)
    #b_device = cuda.device_array_like(b)
    """
    cuda.synchronize()
    
    gpu_time = time.time()
    conv_step_forward3D[blockspergrid,threadsperblock](W_device,Img_device,b_device,Z_device,stride,n_H,n_W,n_C)
    cuda.synchronize()
    k1 = Z_device.copy_to_host()
    print(f"With GPU:{time.time()-gpu_time}")
    

    #CPU
    obj = Layers.ConvLayer()
    cpu_time = time.time()
    Z,_= obj.conv_forward(Img,W,b,stride)            
    k2 = Z[0,:,:,:]
    print(f"With CPU:{time.time()-cpu_time}")

    print(np.array_equal(k1,k2))
    """

    #2D
    #GPU
    W = np.random.randn(3,3,16)
    b = np.random.randn(1,1,16)
    Img = np.random.randn(1080,1920)

    n_H_prev,n_W_prev = Img.shape

    fH,fW = W.shape[0],W.shape[1]
    
    stride = 2
    n_H = int((n_H_prev-fH)/stride)+1
    n_W = int((n_W_prev-fW)/stride)+1
    n_C = 16
    
    Z = np.zeros((n_H,n_W,16))
    
    threadsperblock = (8,8,2)

    blockspergrid_H = int(math.ceil(Z.shape[0]/threadsperblock[0]))
    blockspergrid_W = int(math.ceil(Z.shape[1]/threadsperblock[1]))
    blockspergrid_C = int(math.ceil(Z.shape[2]/threadsperblock[2]))

    blockspergrid = (blockspergrid_H,blockspergrid_W,blockspergrid_C)

    
    W_device = cuda.to_device(W)
    Img_device = cuda.to_device(Img)
    Z_device = cuda.to_device(Z)
    b_device = cuda.to_device(b)
    
    """
    #W_device = cuda.device_array_like(W)
    #Img_device = cuda.device_array_like(Img[0,:,:,:])
    #Z_device = cuda.device_array_like(Z)
    #b_device = cuda.device_array_like(b)
    """
    cuda.synchronize()
    
    gpu_time = time.time()
    conv_step_forward2D[blockspergrid,threadsperblock](W_device,Img_device,b_device,Z_device,stride,n_H,n_W,n_C)
    cuda.synchronize()
    k1 = Z_device.copy_to_host()
    print(f"With GPU:{time.time()-gpu_time}")

    
